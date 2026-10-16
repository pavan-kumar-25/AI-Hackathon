"""Tool-calling agent loop for RideWise Assist."""

from __future__ import annotations

import json
from typing import Any, Callable

from config import MAX_TOOL_ROUNDS
from llm.client import chat_completion
from prompts.system import build_system_prompt
from tools.policy_tool import POLICY_TOOL_SPEC, search_policies
from tools.sql_tool import SQL_TOOL_SPEC, query_db

TOOLS = [SQL_TOOL_SPEC, POLICY_TOOL_SPEC]


def _run_tool(
    name: str,
    arguments: dict[str, Any],
    role: str,
    customer_id: str | None,
) -> dict[str, Any]:
    if name == "query_db":
        return query_db(
            sql=arguments.get("sql", ""),
            role=role,
            customer_id=customer_id,
        )
    if name == "search_policies":
        return search_policies(
            query=arguments.get("query", ""),
            k=int(arguments.get("k", 4) or 4),
        )
    return {"ok": False, "error": f"Unknown tool: {name}"}


def run_agent(
    user_message: str,
    history: list[dict[str, Any]],
    role: str,
    customer_id: str | None,
    on_event: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """
    Run one user turn through the tool-calling loop.

    Returns:
      {
        "reply": str,
        "tool_trace": [...],
        "sources": [...],
        "error": optional str,
      }
    """
    system = build_system_prompt(role, customer_id)
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}]

    for msg in history:
        if msg.get("role") in ("user", "assistant") and msg.get("content"):
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})

    tool_trace: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []

    try:
        for _ in range(MAX_TOOL_ROUNDS):
            response = chat_completion(messages, tools=TOOLS, tool_choice="auto")
            choice = response.choices[0]
            message = choice.message

            tool_calls = getattr(message, "tool_calls", None) or []
            if not tool_calls:
                reply = (message.content or "").strip()
                return {
                    "reply": reply or "I could not produce an answer. Please try rephrasing.",
                    "tool_trace": tool_trace,
                    "sources": sources,
                }

            messages.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in tool_calls
                    ],
                }
            )

            for tc in tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                    result: dict[str, Any] = {
                        "ok": False,
                        "error": "Invalid tool arguments JSON.",
                    }
                else:
                    result = _run_tool(name, args, role, customer_id)

                event = {
                    "tool": name,
                    "arguments": args,
                    "result_ok": bool(result.get("ok")),
                }
                tool_trace.append({**event, "result": result})
                if on_event:
                    on_event(event)

                if name == "search_policies" and result.get("results"):
                    for r in result["results"]:
                        sources.append(
                            {
                                "doc_id": r.get("doc_id"),
                                "source": r.get("source"),
                                "page": r.get("page"),
                            }
                        )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False, default=str),
                    }
                )

        response = chat_completion(messages, tools=None, tool_choice=None)
        reply = (response.choices[0].message.content or "").strip()
        return {
            "reply": reply or "I reached the tool-call limit. Please ask a more specific question.",
            "tool_trace": tool_trace,
            "sources": sources,
        }
    except Exception as exc:  # noqa: BLE001 - surface friendly error to UI
        err = str(exc)
        friendly = err
        low = err.lower()
        if "rate" in low or "429" in low:
            friendly = "The LLM is rate-limited right now. Please wait a moment and try again."
        elif "api_key" in low or "authentication" in low or "401" in low:
            friendly = "LLM authentication failed. Check AZURE_OPENAI_API_KEY in your .env file."
        elif "connection" in low or "getaddrinfo" in low or "resolve" in low:
            friendly = (
                "Cannot reach the NeoStats LLM endpoint. "
                "Check your internet connection and AZURE_OPENAI_BASE_URL."
            )
        return {
            "reply": f"Sorry - I hit an error: {friendly}",
            "tool_trace": tool_trace,
            "sources": sources,
            "error": err,
        }

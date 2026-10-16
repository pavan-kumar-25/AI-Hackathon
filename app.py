"""RideWise Assist - Streamlit chat UI."""

from __future__ import annotations

import streamlit as st

from agent.orchestrator import run_agent
from tools.policy_tool import ensure_index

st.set_page_config(
    page_title="RideWise Assist",
    page_icon="RW",
    layout="centered",
)

st.title("RideWise Assist")
st.caption("Conversational AI for RideWise customers and support agents")


def _init_state() -> None:
    defaults = {
        "messages": [],
        "tool_trace": [],
        "sources": [],
        "role": "customer",
        "customer_id": "CUST0001",
        "index_ready": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()

with st.sidebar:
    st.header("Session")
    role = st.radio(
        "Role",
        options=["customer", "agent"],
        format_func=lambda r: "Customer" if r == "customer" else "Support agent",
        key="role",
    )
    customer_id = None
    if role == "customer":
        customer_id = st.text_input(
            "Customer ID",
            value=st.session_state.get("customer_id") or "CUST0001",
            help="e.g. CUST0001",
        ).strip().upper()
        st.session_state.customer_id = customer_id
    else:
        st.session_state.customer_id = None
        customer_id = None

    if st.button("New conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.tool_trace = []
        st.session_state.sources = []
        st.rerun()

    st.divider()
    if role == "customer":
        st.markdown(f"**Active:** Customer `{customer_id or '-'}`")
    else:
        st.markdown("**Active:** Support agent")

    with st.expander("Transparency - last turn", expanded=False):
        sources = st.session_state.get("sources") or []
        if sources:
            st.markdown("**Policy sources**")
            for s in sources:
                st.write(
                    f"- {s.get('doc_id')} | {s.get('source')} | page {s.get('page')}"
                )
        else:
            st.write("No policy sources yet.")

        trace = st.session_state.get("tool_trace") or []
        if trace:
            st.markdown("**Tools used**")
            for t in trace:
                status = "ok" if t.get("result_ok") else "error"
                st.write(f"- `{t.get('tool')}` ({status})")
                st.json(t.get("arguments", {}), expanded=False)
        else:
            st.write("No tools used yet.")

if not st.session_state.index_ready:
    with st.spinner("Preparing policy index..."):
        try:
            ensure_index()
            st.session_state.index_ready = True
        except Exception as exc:  # noqa: BLE001
            st.warning(f"Policy index not ready: {exc}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Ask about bookings, refunds, late fees, EV charging...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = run_agent(
                user_message=prompt,
                history=st.session_state.messages[:-1],
                role=st.session_state.role,
                customer_id=st.session_state.customer_id
                if st.session_state.role == "customer"
                else None,
            )
        reply = result.get("reply") or ""
        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.tool_trace = [
            {
                "tool": t.get("tool"),
                "arguments": t.get("arguments"),
                "result_ok": t.get("result_ok"),
            }
            for t in (result.get("tool_trace") or [])
        ]
        seen = set()
        uniq = []
        for s in result.get("sources") or []:
            key = (s.get("doc_id"), s.get("source"), s.get("page"))
            if key not in seen:
                seen.add(key)
                uniq.append(s)
        st.session_state.sources = uniq

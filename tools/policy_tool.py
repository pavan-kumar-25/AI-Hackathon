"""Policy retrieval tool."""

from __future__ import annotations

from typing import Any

from rag.store import get_policy_store, reload_policy_store
from rag.ingest import build_index
from config import INDEX_DIR

POLICY_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "search_policies",
        "description": (
            "Search RideWise policy PDFs (rental terms, cancellation/refund v1 & v2, "
            "late return & damage penalties, EV user guide). Returns cited excerpts."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language policy question or keywords.",
                },
                "k": {
                    "type": "integer",
                    "description": "Number of chunks to return (default 4).",
                },
            },
            "required": ["query"],
        },
    },
}


def ensure_index() -> None:
    chunks_path = INDEX_DIR / "chunks.json"
    if not chunks_path.exists():
        build_index()
        reload_policy_store()


def search_policies(query: str, k: int = 4) -> dict[str, Any]:
    ensure_index()
    store = get_policy_store()
    if not store.chunks:
        build_index()
        reload_policy_store()
        store = get_policy_store()

    hits = store.search(query, k=max(1, min(int(k or 4), 8)))
    results = [
        {
            "doc_id": h.get("doc_id"),
            "source": h.get("source"),
            "page": h.get("page"),
            "text": h.get("text"),
            "score": h.get("score"),
        }
        for h in hits
    ]
    return {"ok": True, "results": results, "count": len(results)}

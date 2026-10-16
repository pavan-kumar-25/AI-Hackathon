"""BM25 policy chunk store."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

from config import INDEX_DIR

_TOKEN = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text)]


class PolicyStore:
    def __init__(self, chunks: list[dict[str, Any]]):
        self.chunks = chunks
        self._corpus = [tokenize(c.get("text", "")) for c in chunks]
        self._bm25 = BM25Okapi(self._corpus) if chunks else None

    @classmethod
    def load(cls, index_dir: Path | None = None) -> "PolicyStore":
        index_dir = index_dir or INDEX_DIR
        path = index_dir / "chunks.json"
        if not path.exists():
            return cls([])
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(data.get("chunks", []))

    def search(self, query: str, k: int = 4) -> list[dict[str, Any]]:
        if not self._bm25 or not self.chunks:
            return []
        tokens = tokenize(query)
        if not tokens:
            return []
        scores = self._bm25.get_scores(tokens)
        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True,
        )[:k]
        results = []
        for idx, score in ranked:
            if score <= 0:
                continue
            chunk = dict(self.chunks[idx])
            chunk["score"] = float(score)
            results.append(chunk)
        return results


@lru_cache(maxsize=1)
def get_policy_store() -> PolicyStore:
    return PolicyStore.load()


def reload_policy_store() -> PolicyStore:
    get_policy_store.cache_clear()
    return get_policy_store()

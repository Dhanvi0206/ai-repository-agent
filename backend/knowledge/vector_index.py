from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path


VECTOR_INDEX_PATH = Path("workspace") / "knowledge" / "vector_index.json"


class VectorIndex:
    """Lightweight vector-style store using token frequency similarity."""

    def __init__(self, index_path: Path | None = None) -> None:
        self.index_path = index_path or VECTOR_INDEX_PATH
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

    def add_entry(self, entry_id: str, text: str, metadata: dict) -> None:
        index = self._load_index()
        index[entry_id] = {
            "text": text,
            "metadata": metadata,
            "vector": self._vectorize(text),
        }
        self._save_index(index)

    def search(self, text: str, top_k: int = 3) -> list[dict]:
        query_vector = self._vectorize(text)
        index = self._load_index()
        scored_results: list[dict] = []

        for entry_id, entry in index.items():
            score = _cosine_similarity(query_vector, entry["vector"])
            scored_results.append(
                {
                    "id": entry_id,
                    "score": round(score, 4),
                    "text": entry["text"],
                    "metadata": entry["metadata"],
                }
            )

        return sorted(scored_results, key=lambda item: item["score"], reverse=True)[:top_k]

    def _load_index(self) -> dict:
        if not self.index_path.exists():
            return {}
        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _save_index(self, index: dict) -> None:
        self.index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    def _vectorize(self, text: str) -> dict[str, float]:
        tokens = re.findall(r"[a-zA-Z_]{3,}", text.lower())
        counts = Counter(tokens)
        total = sum(counts.values()) or 1
        return {token: count / total for token, count in counts.items()}


def _cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    shared = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in shared)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)

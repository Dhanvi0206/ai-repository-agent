from __future__ import annotations

from os import cpu_count


class PerformanceOptimizer:
    """Utility helpers for large-repository throughput control."""

    def optimize_chunks(self, code_chunks: list[dict], max_chunks: int = 150) -> list[dict]:
        if len(code_chunks) <= max_chunks:
            return code_chunks
        return code_chunks[:max_chunks]

    def get_optimal_worker_count(self, agent_count: int) -> int:
        available = cpu_count() or 4
        return max(1, min(agent_count, available, 8))

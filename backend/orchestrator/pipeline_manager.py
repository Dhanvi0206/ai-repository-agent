from __future__ import annotations


AGENT_PRIORITY = {
    "security_agent": 1,
    "dependency_agent": 2,
    "code_review_agent": 3,
    "code_quality_agent": 4,
    "documentation_agent": 5,
    "contribution_intelligence_agent": 6,
    "learning_agent": 7,
    "reporting_agent": 8,
}

HIGH_PRIORITY_KEYWORDS = ("auth", "security", "config", "database", "db", "token", "secret")


class PipelineManager:
    """Handles priority scheduling and incremental context selection."""

    def sort_agents(self, agents: list) -> list:
        return sorted(
            agents,
            key=lambda agent: AGENT_PRIORITY.get(agent.agent_name, 99),
        )

    def prioritize_chunks(self, code_chunks: list[dict]) -> list[dict]:
        if not code_chunks:
            return []

        already_ranked = all("importance" in chunk for chunk in code_chunks)
        if already_ranked:
            return sorted(code_chunks, key=lambda chunk: chunk.get("importance", 0), reverse=True)

        return sorted(code_chunks, key=self._chunk_priority_score, reverse=True)

    def build_incremental_batch(self, code_chunks: list[dict], limit: int = 50) -> list[dict]:
        prioritized_chunks = self.prioritize_chunks(code_chunks)
        return prioritized_chunks[:limit] if len(prioritized_chunks) > limit else prioritized_chunks

    def _chunk_priority_score(self, chunk: dict) -> float:
        file_path = chunk.get("file", chunk.get("file_path", "")).lower()
        score = 0.2
        for keyword in HIGH_PRIORITY_KEYWORDS:
            if keyword in file_path:
                score += 0.15
        return score

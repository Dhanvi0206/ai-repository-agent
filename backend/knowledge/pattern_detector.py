from __future__ import annotations

from backend.knowledge.knowledge_store import KnowledgeStore


class PatternDetector:
    """Detect exact and semantically similar patterns from stored knowledge."""

    def __init__(self, knowledge_store: KnowledgeStore) -> None:
        self.knowledge_store = knowledge_store

    def detect_patterns(self, consensus_issues: list) -> list[dict]:
        detected_patterns: list[dict] = []

        for issue in consensus_issues:
            pattern_key = issue.issue.lower().replace(" ", "_")
            exact_pattern = self.knowledge_store.get_patterns().get(pattern_key)
            if exact_pattern:
                detected_patterns.append(
                    {
                        "pattern_detected": pattern_key,
                        "match_type": "exact",
                        "recommended_fix": exact_pattern.get("recommended_fix"),
                        "frequency": exact_pattern.get("frequency", 0),
                    }
                )
                continue

            semantic_matches = self.knowledge_store.suggest_patterns(
                f"{issue.issue} {issue.recommendation}"
            )
            for match in semantic_matches:
                detected_patterns.append(
                    {
                        "pattern_detected": match["metadata"].get("pattern"),
                        "match_type": "semantic",
                        "similarity": match["score"],
                        "recommended_fix": match["metadata"].get("recommended_fix"),
                    }
                )

        return detected_patterns

from __future__ import annotations

from backend.knowledge.knowledge_store import KnowledgeStore


class SimilarityEngine:
    """Find previously analyzed repositories with similar profiles."""

    def __init__(self, knowledge_store: KnowledgeStore) -> None:
        self.knowledge_store = knowledge_store

    def detect_similar_repository(self, repository_context: dict) -> dict:
        repositories = self.knowledge_store.get_repositories()
        current_summary = repository_context.get("summary", {})
        current_languages = set(repository_context.get("metadata", {}).get("languages_used", []))

        best_match = None
        best_score = 0.0
        for repository_name, repository_profile in repositories.items():
            languages = set(repository_profile.get("languages", []))
            score = 0.0
            if repository_profile.get("summary", {}).get("project_type") == current_summary.get("project_type"):
                score += 0.6
            if current_languages and languages:
                score += 0.4 * (len(current_languages & languages) / len(current_languages | languages))
            if score > best_score:
                best_score = score
                best_match = (repository_name, repository_profile)

        if not best_match or best_score < 0.25:
            return {
                "similar_repo_type": current_summary.get("project_type", "unknown"),
                "recommended_checks": current_summary.get("main_modules", []),
                "similarity_score": round(best_score, 2),
            }

        repository_name, repository_profile = best_match
        return {
            "similar_repo_type": repository_profile.get("summary", {}).get("project_type", "unknown"),
            "recommended_checks": repository_profile.get("recommended_checks", []),
            "similar_repository": repository_name,
            "similarity_score": round(best_score, 2),
        }

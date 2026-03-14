from __future__ import annotations

import json
from pathlib import Path

from backend.knowledge.vector_index import VectorIndex


KNOWLEDGE_STORE_PATH = Path("workspace") / "knowledge" / "knowledge_store.json"


class KnowledgeStore:
    """Persist learned patterns and repository profiles across analyses."""

    def __init__(self, store_path: Path | None = None) -> None:
        self.store_path = store_path or KNOWLEDGE_STORE_PATH
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.vector_index = VectorIndex()

    def load(self) -> dict:
        if not self.store_path.exists():
            return {"patterns": {}, "repositories": {}}
        try:
            return json.loads(self.store_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"patterns": {}, "repositories": {}}

    def save(self, payload: dict) -> None:
        self.store_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def store_analysis(self, repository_context: dict, consensus_issues: list) -> dict:
        payload = self.load()
        patterns = payload.setdefault("patterns", {})
        repositories = payload.setdefault("repositories", {})

        for issue in consensus_issues:
            pattern_key = issue.issue.lower().replace(" ", "_")
            pattern_entry = patterns.setdefault(
                pattern_key,
                {
                    "pattern_type": self._infer_pattern_type(issue.detected_by),
                    "pattern": pattern_key,
                    "frequency": 0,
                    "recommended_fix": issue.recommendation,
                    "repositories": [],
                    "sample_files": [],
                },
            )
            pattern_entry["frequency"] += 1
            repository_name = repository_context.get("repository")
            if repository_name and repository_name not in pattern_entry["repositories"]:
                pattern_entry["repositories"].append(repository_name)
            if issue.file_path not in pattern_entry["sample_files"]:
                pattern_entry["sample_files"].append(issue.file_path)
            pattern_entry["recommended_fix"] = issue.recommendation

            self.vector_index.add_entry(
                pattern_key,
                f"{issue.issue} {issue.recommendation} {' '.join(issue.reasoning_chain)}",
                {
                    "pattern": pattern_key,
                    "pattern_type": pattern_entry["pattern_type"],
                    "recommended_fix": issue.recommendation,
                },
            )

        repository_name = repository_context.get("repository", "unknown_repository")
        repositories[repository_name] = {
            "summary": repository_context.get("summary", {}),
            "languages": repository_context.get("metadata", {}).get("languages_used", []),
            "recommended_checks": _recommended_checks(consensus_issues),
        }

        self.save(payload)
        return payload

    def suggest_patterns(self, text: str, top_k: int = 3) -> list[dict]:
        matches = self.vector_index.search(text, top_k=top_k)
        return [match for match in matches if match["score"] >= 0.2]

    def get_patterns(self) -> dict:
        return self.load().get("patterns", {})

    def get_repositories(self) -> dict:
        return self.load().get("repositories", {})

    def _infer_pattern_type(self, detected_by: list[str]) -> str:
        if "security_agent" in detected_by:
            return "security_vulnerability"
        if "dependency_agent" in detected_by:
            return "dependency_vulnerability"
        if "documentation_agent" in detected_by:
            return "documentation_gap"
        return "code_smell"


def _recommended_checks(consensus_issues: list) -> list[str]:
    checks = {issue.issue.lower() for issue in consensus_issues[:5]}
    return sorted(checks)

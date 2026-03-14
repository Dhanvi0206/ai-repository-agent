from __future__ import annotations

import json
from pathlib import Path


KNOWLEDGE_STORE_PATH = Path("backend") / "learning" / "knowledge_store.json"


class KnowledgeLearningEngine:
    """Persist high-level learned patterns from analyzed repositories."""

    def __init__(self, store_path: Path | None = None) -> None:
        self.store_path = store_path or KNOWLEDGE_STORE_PATH
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict:
        if not self.store_path.exists():
            return {"patterns": {}, "repositories": {}}
        try:
            return json.loads(self.store_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"patterns": {}, "repositories": {}}

    def save(self, payload: dict) -> None:
        self.store_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def learn_from_report(self, repository_id: str, repository_report: dict) -> dict:
        payload = self.load()
        patterns = payload.setdefault("patterns", {})
        repositories = payload.setdefault("repositories", {})

        repositories[repository_id] = {
            "repo_health_score": repository_report.get("repo_health_score"),
            "security_score": repository_report.get("security_score"),
            "code_quality_score": repository_report.get("code_quality_score"),
            "documentation_score": repository_report.get("documentation_score"),
            "dependency_score": repository_report.get("dependency_score"),
        }

        for issue in repository_report.get("issues", []):
            pattern_key = issue.get("issue", "unknown_issue").strip().lower().replace(" ", "_")
            pattern_entry = patterns.setdefault(
                pattern_key,
                {
                    "pattern": pattern_key,
                    "display_name": issue.get("issue", "Unknown Issue"),
                    "pattern_type": self._pattern_type(issue),
                    "frequency": 0,
                    "severity": issue.get("severity", "low"),
                    "repositories": [],
                    "sample_files": [],
                },
            )
            pattern_entry["frequency"] += 1
            pattern_entry["severity"] = issue.get("severity", pattern_entry["severity"])
            if repository_id not in pattern_entry["repositories"]:
                pattern_entry["repositories"].append(repository_id)
            file_path = issue.get("file")
            if file_path and file_path not in pattern_entry["sample_files"]:
                pattern_entry["sample_files"].append(file_path)

        self.save(payload)
        return payload

    def get_insights(self) -> dict:
        payload = self.load()
        patterns = list(payload.get("patterns", {}).values())
        patterns.sort(key=lambda item: item.get("frequency", 0), reverse=True)

        knowledge_insights = [
            {
                "pattern": pattern["pattern"],
                "frequency": pattern.get("frequency", 0),
                "severity": pattern.get("severity", "low"),
                "insight": self._pattern_insight(pattern),
            }
            for pattern in patterns[:10]
        ]

        return {
            "knowledge_insights": knowledge_insights,
            "pattern_frequency_tracking": {
                pattern["pattern"]: {
                    "frequency": pattern.get("frequency", 0),
                    "repositories": len(pattern.get("repositories", [])),
                }
                for pattern in patterns[:10]
            },
            "vulnerability_trends": self._trend_summary(patterns),
            "pattern_similarity_detection": self._similar_patterns(patterns),
            "knowledge_driven_recommendations": self._recommendations(patterns),
        }

    def _pattern_type(self, issue: dict) -> str:
        detected_by = set(issue.get("detected_by", []))
        if "security_agent" in detected_by:
            return "security_vulnerability"
        if "dependency_agent" in detected_by:
            return "dependency_risk"
        if "documentation_agent" in detected_by:
            return "documentation_gap"
        if issue.get("issue") in {"Long Function", "High Complexity", "Duplicate Logic"}:
            return "technical_debt"
        return "code_smell"

    def _pattern_insight(self, pattern: dict) -> str:
        pattern_type = pattern.get("pattern_type", "pattern")
        frequency = pattern.get("frequency", 0)
        if pattern_type == "security_vulnerability":
            return f"Most common vulnerability signal detected {frequency} times."
        if pattern_type == "dependency_risk":
            return f"Dependency-related risk has appeared {frequency} times across analyzed repositories."
        if pattern_type == "technical_debt":
            return f"Technical debt pattern repeatedly detected {frequency} times."
        return f"Recurring repository pattern observed {frequency} times."

    def _trend_summary(self, patterns: list[dict]) -> dict:
        vulnerabilities = [
            pattern for pattern in patterns if pattern.get("pattern_type") in {"security_vulnerability", "dependency_risk"}
        ]
        top_pattern = vulnerabilities[0]["pattern"] if vulnerabilities else None
        trend = "stable"
        if vulnerabilities and vulnerabilities[0].get("frequency", 0) >= 5:
            trend = "increasing"
        return {
            "trend": trend,
            "top_vulnerability_pattern": top_pattern,
        }

    def _similar_patterns(self, patterns: list[dict]) -> list[dict]:
        similarity_groups = []
        for pattern in patterns[:10]:
            name = pattern.get("pattern", "")
            if "credential" in name or "secret" in name:
                similarity_groups.append(
                    {
                        "pattern": name,
                        "similarity_group": "credential_exposure",
                    }
                )
            elif "dependency" in name or "vulnerability" in name:
                similarity_groups.append(
                    {
                        "pattern": name,
                        "similarity_group": "dependency_risk",
                    }
                )
            elif "complexity" in name or "long_function" in name:
                similarity_groups.append(
                    {
                        "pattern": name,
                        "similarity_group": "maintainability_risk",
                    }
                )
        return similarity_groups[:10]

    def _recommendations(self, patterns: list[dict]) -> list[str]:
        recommendations: list[str] = []
        for pattern in patterns[:5]:
            pattern_name = pattern.get("pattern", "")
            if "credential" in pattern_name or "secret" in pattern_name:
                recommendations.append("Authentication modules frequently contain security risks. Review secret handling first.")
            elif "dependency" in pattern_name:
                recommendations.append("Dependency vulnerabilities are recurring. Prioritize package upgrade reviews.")
            elif "complexity" in pattern_name or "long_function" in pattern_name:
                recommendations.append("High-complexity modules recur often. Refactoring should be part of the regular maintenance plan.")
            elif "docstring" in pattern_name:
                recommendations.append("Documentation gaps appear repeatedly. Add documentation checks to CI.")
        return list(dict.fromkeys(recommendations))

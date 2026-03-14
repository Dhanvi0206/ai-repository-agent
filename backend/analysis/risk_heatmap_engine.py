from __future__ import annotations

from pathlib import Path


class RiskHeatmapEngine:
    """Build file and module-level repository risk heatmaps."""

    ISSUE_WEIGHTS = {
        "security": 40,
        "quality": 20,
        "dependency": 30,
        "technical_debt": 25,
        "documentation": 10,
    }

    def analyze(self, repository_report: dict, technical_debt_report: dict) -> dict:
        file_risk: dict[str, dict] = {}

        for issue in repository_report.get("issues", []):
            file_path = issue.get("file", "repository")
            issue_bucket = self._classify_issue(issue)
            self._ensure_file(file_risk, file_path)
            file_risk[file_path]["risk_score"] += self.ISSUE_WEIGHTS[issue_bucket]
            file_risk[file_path]["reasons"].append(issue.get("issue", "Issue detected"))

        for debt_entry in technical_debt_report.get("file_level_debt", []):
            file_path = debt_entry["file"]
            self._ensure_file(file_risk, file_path)
            debt_bonus = round((debt_entry.get("debt_score", 0) / 100) * self.ISSUE_WEIGHTS["technical_debt"])
            file_risk[file_path]["risk_score"] += debt_bonus
            file_risk[file_path]["reasons"].extend(debt_entry.get("reasons", []))

        risk_heatmap = []
        module_scores: dict[str, int] = {}
        clusters: dict[str, list[str]] = {}

        for file_path, data in sorted(
            file_risk.items(),
            key=lambda item: item[1]["risk_score"],
            reverse=True,
        ):
            score = min(data["risk_score"], 100)
            module = self._module_name(file_path)
            level = self._risk_level(score)
            unique_reasons = list(dict.fromkeys(data["reasons"]))

            risk_heatmap.append(
                {
                    "file": file_path,
                    "risk_score": score,
                    "risk_level": level,
                    "module": module,
                    "reasons": unique_reasons[:4],
                }
            )
            module_scores[module] = max(module_scores.get(module, 0), score)
            clusters.setdefault(module, []).append(file_path)

        module_heatmap = [
            {
                "module": module,
                "risk_score": score,
                "risk_level": self._risk_level(score),
                "files": clusters.get(module, [])[:5],
            }
            for module, score in sorted(module_scores.items(), key=lambda item: item[1], reverse=True)
        ]

        return {
            "risk_heatmap": risk_heatmap[:25],
            "module_heatmap": module_heatmap[:10],
            "visual_risk_data": {
                "labels": [entry["file"] for entry in risk_heatmap[:10]],
                "scores": [entry["risk_score"] for entry in risk_heatmap[:10]],
                "levels": [entry["risk_level"] for entry in risk_heatmap[:10]],
            },
            "risk_clusters": [
                {
                    "module": module,
                    "risk_level": self._risk_level(score),
                    "affected_files": clusters.get(module, [])[:5],
                }
                for module, score in sorted(module_scores.items(), key=lambda item: item[1], reverse=True)
                if len(clusters.get(module, [])) >= 2
            ][:8],
        }

    def _ensure_file(self, file_risk: dict[str, dict], file_path: str) -> None:
        file_risk.setdefault(
            file_path,
            {
                "risk_score": 0,
                "reasons": [],
            },
        )

    def _classify_issue(self, issue: dict) -> str:
        detected_by = set(issue.get("detected_by", []))
        if "security_agent" in detected_by:
            return "security"
        if "dependency_agent" in detected_by:
            return "dependency"
        if "documentation_agent" in detected_by:
            return "documentation"
        return "quality"

    def _risk_level(self, score: int) -> str:
        if score > 80:
            return "high"
        if score >= 40:
            return "medium"
        return "low"

    def _module_name(self, file_path: str) -> str:
        parts = [part for part in Path(file_path).parts if part not in {"src", "tests", "backend", "app"}]
        if not parts:
            return "repository"
        if len(parts) > 1:
            return parts[-2].replace("_", " ")
        return Path(parts[-1]).stem.replace("_", " ")

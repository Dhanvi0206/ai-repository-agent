from __future__ import annotations


class FixPriorityEngine:
    """Rank repository issues by severity, confidence, and likely impact."""

    SEVERITY_WEIGHTS = {
        "critical": 100,
        "high": 70,
        "medium": 40,
        "low": 20,
    }

    def prioritize(self, repository_report: dict) -> dict:
        ranked_issues = []
        seen: set[tuple[str | None, str | None]] = set()
        for issue in repository_report.get("issues", []):
            issue_key = (issue.get("file"), issue.get("issue"))
            if issue_key in seen:
                continue
            seen.add(issue_key)
            priority_score = self._priority_score(issue)
            ranked_issues.append(
                {
                    "issue": issue.get("issue"),
                    "file": issue.get("file"),
                    "severity": issue.get("severity"),
                    "priority_score": priority_score,
                    "urgency": self._urgency(priority_score),
                    "impact_explanation": self._impact_explanation(issue),
                    "recommendation": issue.get("fix", {}).get("summary"),
                    "confidence": issue.get("confidence", 0.0),
                }
            )

        ranked_issues.sort(
            key=lambda item: (
                item["priority_score"],
                item.get("confidence", 0.0),
            ),
            reverse=True,
        )

        for index, issue in enumerate(ranked_issues, start=1):
            issue["rank"] = index

        return {
            "priority_issues": ranked_issues[:25],
            "top_critical_chart": {
                "labels": [issue["issue"] for issue in ranked_issues[:5]],
                "scores": [issue["priority_score"] for issue in ranked_issues[:5]],
                "urgency": [issue["urgency"] for issue in ranked_issues[:5]],
            },
        }

    def _priority_score(self, issue: dict) -> int:
        severity = issue.get("severity", "low")
        base = self.SEVERITY_WEIGHTS.get(severity, 20)
        confidence_bonus = round((issue.get("confidence", 0.0) or 0.0) * 10)
        risk_bonus = 10 if issue.get("risk_level") == "high" else 5 if issue.get("risk_level") == "medium" else 0
        return min(base + confidence_bonus + risk_bonus, 100)

    def _urgency(self, score: int) -> str:
        if score >= 85:
            return "Immediate"
        if score >= 50:
            return "Recommended"
        return "Optional"

    def _impact_explanation(self, issue: dict) -> str:
        detected_by = set(issue.get("detected_by", []))
        if "security_agent" in detected_by:
            return "This issue may expose sensitive credentials or increase security risk."
        if "dependency_agent" in detected_by:
            return "This issue may leave the repository exposed to dependency-related vulnerabilities."
        if "code_quality_agent" in detected_by or "code_review_agent" in detected_by:
            return "This issue increases maintainability cost and can slow future development."
        if "documentation_agent" in detected_by:
            return "This issue can reduce onboarding speed and make debugging harder."
        return "This issue should be reviewed to reduce repository risk and maintenance overhead."

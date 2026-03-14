from __future__ import annotations


WEIGHTS = {
    "security_score": 0.4,
    "quality_score": 0.3,
    "documentation_score": 0.15,
    "dependency_score": 0.15,
}


class ExplainableScoreEngine:
    """Build developer-friendly explanations for repository health scoring."""

    def build_score_explanation(self, repository_report: dict) -> dict:
        security_score = repository_report.get("security_score", 0) or 0
        quality_score = repository_report.get("code_quality_score", 0) or 0
        documentation_score = repository_report.get("documentation_score", 0) or 0
        dependency_score = repository_report.get("dependency_score", 0) or 0

        repo_health_score = round(
            (security_score * WEIGHTS["security_score"])
            + (quality_score * WEIGHTS["quality_score"])
            + (documentation_score * WEIGHTS["documentation_score"])
            + (dependency_score * WEIGHTS["dependency_score"]),
            2,
        )

        issues = repository_report.get("issues", [])
        most_impactful_issue = self._most_impactful_issue(issues)

        reasoning = [
            self._build_security_reasoning(repository_report),
            self._build_quality_reasoning(repository_report),
            self._build_documentation_reasoning(repository_report),
            self._build_dependency_reasoning(repository_report),
        ]

        explanation = {
            "repo_health_score": repo_health_score,
            "weights": {
                "security": 0.4,
                "quality": 0.3,
                "documentation": 0.15,
                "dependency": 0.15,
            },
            "score_breakdown": {
                "security_score": security_score,
                "quality_score": quality_score,
                "documentation_score": documentation_score,
                "dependency_score": dependency_score,
            },
            "reasoning": reasoning,
            "most_impactful_issue": most_impactful_issue,
            "developer_friendly_explanation": self._developer_friendly_explanation(
                most_impactful_issue
            ),
            "improvement_suggestions": self._improvement_suggestions(repository_report),
        }
        return explanation

    def _build_security_reasoning(self, repository_report: dict) -> str:
        security_issues = repository_report.get("security_report", {}).get("security_issues", [])
        if not security_issues:
            return "Security score stayed high because no major security vulnerabilities were confirmed."
        top_issue = security_issues[0]
        return (
            f"Security score was reduced due to {top_issue['issue'].lower()} in "
            f"{top_issue['file']}."
        )

    def _build_quality_reasoning(self, repository_report: dict) -> str:
        quality_issues = repository_report.get("code_quality_report", {}).get("code_quality_issues", [])
        if not quality_issues:
            return "Code quality score remained stable because no major maintainability issues were found."
        top_issue = quality_issues[0]
        return (
            f"Code quality score was affected by {top_issue['issue'].lower()} "
            f"in {top_issue['file']}."
        )

    def _build_documentation_reasoning(self, repository_report: dict) -> str:
        documentation_issues = repository_report.get("documentation_report", {}).get("documentation_issues", [])
        if not documentation_issues:
            return "Documentation score remained strong because the repository has adequate documentation coverage."
        return (
            f"Documentation score was reduced because {documentation_issues[0].lower()}."
        )

    def _build_dependency_reasoning(self, repository_report: dict) -> str:
        dependency_risks = repository_report.get("dependency_risk_report", {}).get("dependency_risks", [])
        if not dependency_risks:
            return "Dependency score remained high because no risky dependencies were confirmed."
        top_issue = dependency_risks[0]
        return (
            f"Dependency score was reduced due to {top_issue['vulnerability'].lower()} "
            f"linked to {top_issue['dependency']}."
        )

    def _most_impactful_issue(self, issues: list[dict]) -> dict | None:
        if not issues:
            return None
        severity_weight = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        top_issue = max(
            issues,
            key=lambda issue: (
                severity_weight.get(issue.get("severity", "low"), 0),
                issue.get("confidence", 0),
            ),
        )
        point_drop = {
            "critical": 25,
            "high": 10,
            "medium": 5,
            "low": 2,
        }.get(top_issue.get("severity", "low"), 0)
        return {
            "issue": top_issue["issue"],
            "file": top_issue["file"],
            "severity": top_issue["severity"],
            "impact": f"{top_issue['issue']} caused an estimated {point_drop} point drop.",
            "reasoning": top_issue["reasoning"],
            "fix": top_issue["fix"]["summary"],
        }

    def _developer_friendly_explanation(self, impactful_issue: dict | None) -> str:
        if not impactful_issue:
            return "The repository health score is strong because no major issues were detected."
        return (
            f"{impactful_issue['issue']} was detected in {impactful_issue['file']}. "
            "This kind of issue can increase maintenance or security risk if left unresolved."
        )

    def _improvement_suggestions(self, repository_report: dict) -> list[str]:
        issues = repository_report.get("issues", [])
        suggestions: list[str] = []
        for issue in issues[:5]:
            suggestion = issue.get("fix", {}).get("summary")
            if suggestion and suggestion not in suggestions:
                suggestions.append(suggestion)
        return suggestions

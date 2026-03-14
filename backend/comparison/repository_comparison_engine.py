from __future__ import annotations


class RepositoryComparisonEngine:
    """Compare two repository reports and generate dashboard-friendly insights."""

    SCORE_FIELDS = (
        ("repo_health_score", "overall health"),
        ("security_score", "security"),
        ("code_quality_score", "code quality"),
        ("documentation_score", "documentation"),
        ("dependency_score", "dependency"),
    )

    def compare(
        self,
        repo_a_id: str,
        repo_a_report: dict,
        repo_b_id: str,
        repo_b_report: dict,
    ) -> dict:
        comparison_summary: list[str] = []
        recommendations: list[str] = []

        score_pairs = {
            "repoA_health": repo_a_report.get("repo_health_score", 0),
            "repoB_health": repo_b_report.get("repo_health_score", 0),
            "repoA_security": repo_a_report.get("security_score", 0),
            "repoB_security": repo_b_report.get("security_score", 0),
            "repoA_quality": repo_a_report.get("code_quality_score", 0),
            "repoB_quality": repo_b_report.get("code_quality_score", 0),
            "repoA_documentation": repo_a_report.get("documentation_score", 0),
            "repoB_documentation": repo_b_report.get("documentation_score", 0),
            "repoA_dependency": repo_a_report.get("dependency_score", 0),
            "repoB_dependency": repo_b_report.get("dependency_score", 0),
        }

        for field, label in self.SCORE_FIELDS:
            repo_a_value = repo_a_report.get(field, 0) or 0
            repo_b_value = repo_b_report.get(field, 0) or 0
            if repo_a_value > repo_b_value:
                comparison_summary.append(
                    f"{repo_a_id} has stronger {label} metrics than {repo_b_id}."
                )
            elif repo_b_value > repo_a_value:
                comparison_summary.append(
                    f"{repo_b_id} has stronger {label} metrics than {repo_a_id}."
                )
            else:
                comparison_summary.append(
                    f"{repo_a_id} and {repo_b_id} are tied on {label}."
                )

        risk_comparison = self._build_risk_comparison(
            repo_a_id,
            repo_a_report,
            repo_b_id,
            repo_b_report,
        )
        recommendations.extend(
            self._build_recommendations(repo_a_id, repo_a_report, repo_b_id, repo_b_report)
        )

        return {
            "repositories": {
                "repoA": repo_a_id,
                "repoB": repo_b_id,
            },
            "comparison_summary": comparison_summary,
            "comparison_scores": score_pairs,
            "visual_comparison": {
                "labels": ["health", "security", "quality", "documentation", "dependency"],
                "repoA": [
                    repo_a_report.get("repo_health_score", 0),
                    repo_a_report.get("security_score", 0),
                    repo_a_report.get("code_quality_score", 0),
                    repo_a_report.get("documentation_score", 0),
                    repo_a_report.get("dependency_score", 0),
                ],
                "repoB": [
                    repo_b_report.get("repo_health_score", 0),
                    repo_b_report.get("security_score", 0),
                    repo_b_report.get("code_quality_score", 0),
                    repo_b_report.get("documentation_score", 0),
                    repo_b_report.get("dependency_score", 0),
                ],
            },
            "risk_comparison": risk_comparison,
            "recommendations": list(dict.fromkeys(recommendations)),
        }

    def _build_risk_comparison(
        self,
        repo_a_id: str,
        repo_a_report: dict,
        repo_b_id: str,
        repo_b_report: dict,
    ) -> dict:
        security_risk_a = 100 - (repo_a_report.get("security_score", 0) or 0)
        security_risk_b = 100 - (repo_b_report.get("security_score", 0) or 0)
        dependency_risk_a = 100 - (repo_a_report.get("dependency_score", 0) or 0)
        dependency_risk_b = 100 - (repo_b_report.get("dependency_score", 0) or 0)

        return {
            "higher_security_risk": (
                repo_a_id
                if security_risk_a > security_risk_b
                else repo_b_id
                if security_risk_b > security_risk_a
                else "equal_risk"
            ),
            "higher_dependency_risk": (
                repo_a_id
                if dependency_risk_a > dependency_risk_b
                else repo_b_id
                if dependency_risk_b > dependency_risk_a
                else "equal_risk"
            ),
            "security_risk_gap": abs(round(security_risk_a - security_risk_b, 2)),
            "dependency_risk_gap": abs(round(dependency_risk_a - dependency_risk_b, 2)),
        }

    def _build_recommendations(
        self,
        repo_a_id: str,
        repo_a_report: dict,
        repo_b_id: str,
        repo_b_report: dict,
    ) -> list[str]:
        recommendations: list[str] = []
        for repo_id, report in ((repo_a_id, repo_a_report), (repo_b_id, repo_b_report)):
            if (report.get("dependency_score", 0) or 0) < 80:
                recommendations.append(
                    f"{repo_id} should update dependencies to improve dependency and security resilience."
                )
            if (report.get("security_score", 0) or 0) < 80:
                recommendations.append(
                    f"{repo_id} should address security findings to reduce future risk exposure."
                )
            if (report.get("code_quality_score", 0) or 0) < 75:
                recommendations.append(
                    f"{repo_id} would benefit from refactoring high-complexity modules to improve maintainability."
                )
            if (report.get("documentation_score", 0) or 0) < 75:
                recommendations.append(
                    f"{repo_id} should improve documentation coverage to support onboarding and maintenance."
                )
        return recommendations

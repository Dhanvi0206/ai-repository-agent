from backend.intelligence.developer_reputation import calculate_developer_reputation
from backend.intelligence.intelligence_summary import generate_intelligence_summary
from backend.intelligence.maintainability_index import calculate_maintainability_index
from backend.intelligence.repo_health_score import calculate_repo_health_score
from backend.intelligence.trend_analysis import analyze_health_trend
from backend.models.response_models import HealthScore


class HealthScoreCalculator:
    """Calculates repository health and quality scores."""

    def calculate_score(
        self,
        repository_context: dict,
        consensus_issues: list,
    ) -> HealthScore:
        health_metrics = calculate_repo_health_score(
            consensus_issues,
            repository_context.get("security_report"),
        )
        maintainability_metrics = calculate_maintainability_index(consensus_issues)
        developer_metrics = calculate_developer_reputation(
            repository_context,
            health_metrics,
            consensus_issues,
        )
        trend_metrics = analyze_health_trend(
            repository_context.get("repository", "unknown_repository"),
            health_metrics["repo_health_score"],
        )
        intelligence_summary = generate_intelligence_summary(
            health_metrics,
            developer_metrics,
            trend_metrics,
        )

        return HealthScore(
            score=health_metrics["repo_health_score"],
            status="calculated",
            message="Repository intelligence metrics calculated successfully.",
            security_score=health_metrics["security_score"],
            code_quality_score=health_metrics["code_quality_score"],
            documentation_score=health_metrics["documentation_score"],
            dependency_score=health_metrics["dependency_score"],
            maintainability_score=maintainability_metrics["maintainability_score"],
            developer_reputation_score=developer_metrics["reputation_score"],
            health_trend=trend_metrics["health_trend"],
            intelligence_summary=intelligence_summary,
        )

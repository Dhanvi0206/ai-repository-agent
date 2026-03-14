from __future__ import annotations


def generate_intelligence_summary(
    health_metrics: dict,
    developer_reputation: dict,
    trend_metrics: dict,
) -> dict:
    """Build a concise frontend-friendly intelligence summary."""
    return {
        "repo_health_score": health_metrics.get("repo_health_score"),
        "critical_issues": health_metrics.get("critical_issues", 0),
        "high_risk_dependencies": health_metrics.get("high_risk_dependencies", 0),
        "top_contributor": developer_reputation.get("developer"),
        "developer_reputation_score": developer_reputation.get("reputation_score"),
        "pr_acceptance_rate": developer_reputation.get("pr_acceptance_rate"),
        "bug_frequency": developer_reputation.get("bug_frequency"),
        "repo_trend": trend_metrics.get("health_trend"),
    }

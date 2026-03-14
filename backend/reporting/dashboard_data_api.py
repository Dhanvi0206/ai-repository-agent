from __future__ import annotations

from backend.reporting.report_generator import generate_repository_report


def build_repository_report(analysis_response) -> dict:
    return generate_repository_report(analysis_response)


def build_issue_details(analysis_response, issue_key: str | None = None) -> dict:
    report = generate_repository_report(analysis_response)
    issues = report["issues"]
    if issue_key:
        issues = [issue for issue in issues if f"{issue['file']}:{issue['line'] or 0}:{issue['issue']}" == issue_key]
    return {
        "repository": report["repository"],
        "issues": issues,
    }


def build_developer_report(analysis_response) -> dict:
    report = generate_repository_report(analysis_response)
    developer_insights = report.get("developer_intelligence", {}).get(
        "developer_insights",
        [],
    )
    summary = report.get("repository_scores", {}).get("intelligence_summary", {})
    return {
        "repository": report["repository"],
        "developer_insights": developer_insights,
        "knowledge_insights": report["knowledge_insights"].get("knowledge_metrics", {}),
        "health_trend": report.get("repository_scores", {}).get("health_trend"),
        "summary": {
            "repo_health_score": report.get("repo_health_score"),
            "critical_issues": report.get("critical_issues", 0),
            "high_risk_dependencies": len(
                report.get("dependency_risk_report", {}).get("dependency_risks", [])
            ),
            "top_contributor": summary.get("top_contributor"),
            "repo_trend": summary.get("repo_trend"),
        },
    }

from __future__ import annotations


WEIGHTS = {
    "security_score": 0.35,
    "code_quality_score": 0.25,
    "dependency_score": 0.20,
    "documentation_score": 0.20,
}

SEVERITY_PENALTIES = {
    "critical": 25,
    "high": 15,
    "medium": 5,
    "low": 2,
}


def calculate_repo_health_score(consensus_issues: list, security_report: dict | None = None) -> dict:
    """Compute repository health metrics from collaboration-backed issues."""
    security_issues = [
        issue for issue in consensus_issues if "security_agent" in issue.detected_by
    ]
    code_quality_issues = [
        issue
        for issue in consensus_issues
        if {"code_quality_agent", "code_review_agent"} & set(issue.detected_by)
    ]
    documentation_issues = [
        issue for issue in consensus_issues if "documentation_agent" in issue.detected_by
    ]
    dependency_issues = [
        issue for issue in consensus_issues if "dependency_agent" in issue.detected_by
    ]

    security_score = _calculate_security_score(security_issues, security_report)
    code_quality_score = _apply_penalties(100, code_quality_issues, 5)
    documentation_score = _apply_penalties(100, documentation_issues, 3)
    dependency_score = _apply_penalties(100, dependency_issues, 8)

    repo_health_score = round(
        (security_score * WEIGHTS["security_score"])
        + (code_quality_score * WEIGHTS["code_quality_score"])
        + (dependency_score * WEIGHTS["dependency_score"])
        + (documentation_score * WEIGHTS["documentation_score"]),
        2,
    )

    return {
        "repo_health_score": repo_health_score,
        "security_score": security_score,
        "code_quality_score": code_quality_score,
        "documentation_score": documentation_score,
        "dependency_score": dependency_score,
        "critical_issues": sum(1 for issue in consensus_issues if issue.severity == "critical"),
        "high_risk_dependencies": sum(1 for issue in dependency_issues if issue.risk_level in {"high", "critical"}),
        "secrets_found": (security_report or {}).get("secrets_found", 0),
        "dangerous_patterns": (security_report or {}).get("dangerous_patterns", 0),
        "dependency_vulnerabilities": (security_report or {}).get("dependency_vulnerabilities", 0),
    }


def _apply_penalties(base_score: int, issues: list, issue_penalty: int) -> float:
    score = float(base_score - (len(issues) * issue_penalty))
    for issue in issues:
        score -= SEVERITY_PENALTIES.get(issue.severity, 0)
    return round(max(score, 0.0), 2)


def _calculate_security_score(security_issues: list, security_report: dict | None) -> float:
    if security_report and security_report.get("score") is not None:
        issue_penalties = sum(SEVERITY_PENALTIES.get(issue.severity, 0) * 0.25 for issue in security_issues)
        return round(max(float(security_report["score"]) - issue_penalties, 0.0), 2)
    return _apply_penalties(100, security_issues, 10)

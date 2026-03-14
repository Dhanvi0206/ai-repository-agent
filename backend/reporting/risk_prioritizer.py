from __future__ import annotations


RISK_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def prioritize_issues(issues: list) -> dict:
    """Sort issues by risk and compute issue counts per risk level."""
    sorted_issues = sorted(
        issues,
        key=lambda issue: (
            RISK_ORDER.get(issue.risk_level, 99),
            -issue.confidence,
        ),
    )

    counts = {
        "critical_issues": sum(1 for issue in issues if issue.risk_level == "critical"),
        "high_issues": sum(1 for issue in issues if issue.risk_level == "high"),
        "medium_issues": sum(1 for issue in issues if issue.risk_level == "medium"),
        "low_issues": sum(1 for issue in issues if issue.risk_level == "low"),
    }

    return {"issues": sorted_issues, "counts": counts}

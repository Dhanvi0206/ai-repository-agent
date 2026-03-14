from __future__ import annotations


def calculate_maintainability_index(consensus_issues: list) -> dict:
    """Estimate maintainability from code quality and review issues."""
    maintainability_score = 100.0

    for issue in consensus_issues:
        issue_name = issue.issue.lower()
        if "high complexity" in issue_name:
            maintainability_score -= 12
        elif "long function" in issue_name:
            maintainability_score -= 10
        elif "duplicate logic" in issue_name:
            maintainability_score -= 8
        elif "weak variable naming" in issue_name:
            maintainability_score -= 4

    return {
        "maintainability_score": round(max(maintainability_score, 0.0), 2)
    }

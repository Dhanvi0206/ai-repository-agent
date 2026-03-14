from __future__ import annotations

import subprocess


def calculate_developer_reputation(
    repository_context: dict,
    health_metrics: dict,
    consensus_issues: list,
) -> dict:
    """Estimate contributor reputation using local git history and repository quality signals."""
    local_path = repository_context.get("local_path")
    author_counts = _collect_author_counts(local_path) if local_path else {}

    if not author_counts:
        return {
            "developer": "unknown",
            "reputation_score": 0.5,
            "pr_acceptance_rate": 0.75,
            "bug_frequency": 0.0,
            "commit_consistency": 0.0,
            "risk_flag": "insufficient_data",
        }

    top_author, commit_count = max(author_counts.items(), key=lambda item: item[1])
    total_commits = sum(author_counts.values())
    commit_consistency = round(commit_count / max(total_commits, 1), 2)

    issue_count = len(consensus_issues)
    bug_frequency = round(min(issue_count / max(total_commits, 1), 1.0), 2)
    pr_acceptance_rate = round(max(0.55, 1.0 - (bug_frequency * 0.4)), 2)
    code_quality_score = health_metrics.get("code_quality_score", 70) / 100
    documentation_score = health_metrics.get("documentation_score", 70) / 100

    reputation_score = round(
        (pr_acceptance_rate * 0.4)
        + (code_quality_score * 0.3)
        + (documentation_score * 0.1)
        + (commit_consistency * 0.2),
        2,
    )

    risk_flag = "none"
    if bug_frequency >= 0.5:
        risk_flag = "high_bug_rate"
    elif reputation_score < 0.6:
        risk_flag = "low_reputation_score"

    return {
        "developer": top_author,
        "reputation_score": reputation_score,
        "pr_acceptance_rate": pr_acceptance_rate,
        "bug_frequency": bug_frequency,
        "commit_consistency": commit_consistency,
        "risk_flag": risk_flag,
    }


def _collect_author_counts(local_path: str) -> dict[str, int]:
    command = [
        "git",
        "-c",
        "safe.directory=*",
        "-C",
        local_path,
        "log",
        "--format=%an",
        "-n",
        "50",
    ]
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return {}

    author_counts: dict[str, int] = {}
    for line in result.stdout.splitlines():
        author = line.strip() or "unknown"
        author_counts[author] = author_counts.get(author, 0) + 1
    return author_counts

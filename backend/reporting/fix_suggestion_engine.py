from __future__ import annotations


FIX_EXAMPLES = {
    "hardcoded api key": {
        "before": 'API_KEY = "123456"',
        "after": 'API_KEY = os.getenv("API_KEY")',
    },
    "hardcoded credential": {
        "before": 'password = "secret"',
        "after": 'password = os.getenv("APP_PASSWORD")',
    },
}


def build_fix_suggestion(issue, learned_suggestions: list[dict]) -> dict:
    """Build actionable fix guidance for frontend display."""
    normalized_issue = issue.issue.lower()
    learned_fix = next(
        (
            suggestion["suggested_fix"]
            for suggestion in learned_suggestions
            if suggestion.get("issue", "").lower() == normalized_issue
            and suggestion.get("file_path") == issue.file_path
        ),
        issue.recommendation,
    )

    example = FIX_EXAMPLES.get(normalized_issue)
    return {
        "summary": learned_fix,
        "before": example.get("before") if example else None,
        "after": example.get("after") if example else None,
    }

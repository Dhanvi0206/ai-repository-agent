from __future__ import annotations


class FixSuggestionEngine:
    """Generate fix suggestions from learned patterns and current issues."""

    def suggest_fixes(self, consensus_issues: list, detected_patterns: list[dict]) -> list[dict]:
        pattern_lookup = {
            entry["pattern_detected"]: entry.get("recommended_fix")
            for entry in detected_patterns
            if entry.get("recommended_fix")
        }

        suggestions: list[dict] = []
        for issue in consensus_issues:
            pattern_key = issue.issue.lower().replace(" ", "_")
            suggestions.append(
                {
                    "issue": issue.issue,
                    "suggested_fix": pattern_lookup.get(pattern_key, issue.recommendation),
                    "file_path": issue.file_path,
                }
            )
        return suggestions

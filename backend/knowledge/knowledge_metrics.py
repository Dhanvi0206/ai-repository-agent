from __future__ import annotations


def calculate_knowledge_metrics(patterns: dict) -> dict:
    """Report knowledge growth and most frequent learned patterns."""
    if not patterns:
        return {
            "patterns_learned": 0,
            "most_common_vulnerability": None,
            "most_common_code_smell": None,
        }

    sorted_patterns = sorted(
        patterns.values(),
        key=lambda pattern: pattern.get("frequency", 0),
        reverse=True,
    )
    vulnerabilities = [
        pattern for pattern in sorted_patterns if "vulnerability" in pattern.get("pattern_type", "")
    ]
    code_smells = [
        pattern for pattern in sorted_patterns if pattern.get("pattern_type") == "code_smell"
    ]

    return {
        "patterns_learned": len(patterns),
        "most_common_vulnerability": vulnerabilities[0]["pattern"] if vulnerabilities else None,
        "most_common_code_smell": code_smells[0]["pattern"] if code_smells else None,
    }

from __future__ import annotations


def build_explanation(issue) -> str:
    """Translate technical findings into developer-friendly language."""
    explanation = (
        f"{issue.issue} was identified in {issue.file_path}. "
        f"This issue is marked as {issue.severity} severity with {issue.confidence:.2f} confidence."
    )

    if issue.reasoning_chain:
        explanation += " " + " ".join(issue.reasoning_chain[:2])

    if issue.issue.lower().startswith("hardcoded"):
        explanation += " Sensitive values stored in code can be exposed if the repository is shared."
    elif "complexity" in issue.issue.lower():
        explanation += " High complexity can slow development and make bugs harder to fix."

    return explanation

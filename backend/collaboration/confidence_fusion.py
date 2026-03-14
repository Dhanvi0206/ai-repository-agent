from __future__ import annotations


AGENT_WEIGHTS = {
    "security_agent": 0.35,
    "dependency_agent": 0.25,
    "code_quality_agent": 0.15,
    "code_review_agent": 0.1,
    "contribution_intelligence_agent": 0.1,
    "learning_agent": 0.08,
    "documentation_agent": 0.05,
}


def fuse_confidence(agent_confidences: list[tuple[str, float]]) -> float:
    """Fuse multi-agent confidence using weighted evidence plus agreement bonus."""
    if not agent_confidences:
        return 0.0

    weighted_sum = 0.0
    total_weight = 0.0
    for agent_name, confidence in agent_confidences:
        weight = AGENT_WEIGHTS.get(agent_name, 0.05)
        weighted_sum += weight * confidence
        total_weight += weight

    base_confidence = weighted_sum / total_weight if total_weight else 0.0
    agreement_bonus = min(max(len(agent_confidences) - 1, 0) * 0.04, 0.12)
    return round(min(base_confidence + agreement_bonus, 0.99), 2)

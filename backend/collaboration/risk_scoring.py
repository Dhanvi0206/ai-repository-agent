from __future__ import annotations


SEVERITY_BASE = {
    "low": 0.2,
    "medium": 0.45,
    "high": 0.72,
    "critical": 0.9,
}


def score_risk_level(severity: str, confidence: float, confirmations: int) -> str:
    """Calculate final risk level from severity, confidence, and agent agreement."""
    score = SEVERITY_BASE.get(severity, 0.4)
    score += min(confirmations * 0.07, 0.21)
    score += confidence * 0.2

    if score >= 1.0:
        return "critical"
    if score >= 0.8:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"

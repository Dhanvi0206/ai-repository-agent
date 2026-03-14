from __future__ import annotations

import json
from pathlib import Path


HISTORY_PATH = Path("workspace") / "intelligence" / "repo_health_history.json"


def analyze_health_trend(repository_name: str, current_score: float) -> dict:
    """Track repository health over time and classify the current trend."""
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    history = _load_history()
    repository_history = history.get(repository_name, [])
    previous_score = repository_history[-1] if repository_history else None

    if previous_score is None:
        trend = "stable"
    elif current_score > previous_score:
        trend = "improving"
    elif current_score < previous_score:
        trend = "declining"
    else:
        trend = "stable"

    repository_history.append(current_score)
    history[repository_name] = repository_history[-20:]
    HISTORY_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")

    return {
        "previous_score": previous_score,
        "current_score": current_score,
        "health_trend": trend,
    }


def _load_history() -> dict:
    if not HISTORY_PATH.exists():
        return {}
    try:
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

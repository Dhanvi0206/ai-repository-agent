from __future__ import annotations


HIGH_PRIORITY_KEYWORDS = {
    "auth": 0.35,
    "security": 0.35,
    "config": 0.25,
    "database": 0.25,
    "db": 0.2,
    "login": 0.25,
    "token": 0.2,
    "secret": 0.2,
    "settings": 0.15,
}


def rank_chunks(contexts: list[dict]) -> list[dict]:
    """Rank chunk contexts so agents can analyze the most important code first."""
    ranked_contexts: list[dict] = []

    for context in contexts:
        file_path = context["file"].lower()
        importance = 0.2

        for keyword, weight in HIGH_PRIORITY_KEYWORDS.items():
            if keyword in file_path:
                importance += weight

        if context.get("imports"):
            importance += min(len(context["imports"]) * 0.03, 0.15)
        if context.get("classes"):
            importance += 0.1
        if context.get("functions"):
            importance += min(len(context["functions"]) * 0.02, 0.1)

        ranked_context = dict(context)
        ranked_context["importance"] = round(min(importance, 1.0), 2)
        ranked_contexts.append(ranked_context)

    return sorted(ranked_contexts, key=lambda item: item["importance"], reverse=True)

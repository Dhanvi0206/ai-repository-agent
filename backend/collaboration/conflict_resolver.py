from __future__ import annotations

from backend.models.reasoning_models import DebateResult


class ConflictResolver:
    """Resolve collaboration conflicts using debate outcomes and peer support."""

    def resolve(self, aggregated_results: list[dict], debates: list[DebateResult]) -> list[dict]:
        debate_lookup = {debate.issue_key: debate for debate in debates}
        resolved_results: list[dict] = []

        for result in aggregated_results:
            debate = debate_lookup.get(result["issue_key"])
            if not debate:
                result["status"] = "warning"
                result["reasoning_chain"].append(
                    "Conflict resolver found no debate evidence; flagged for review."
                )
                resolved_results.append(result)
                continue

            if debate.status == "rejected":
                result["status"] = "discarded"
                result["reasoning_chain"].append(debate.outcome)
            elif debate.status == "warning":
                result["status"] = "warning"
                result["reasoning_chain"].append(debate.outcome)
            else:
                result["status"] = "accepted"
                result["reasoning_chain"].append(debate.outcome)

            result["verified_by"] = debate.supporting_agents
            result["opposed_by"] = debate.opposing_agents
            result["confidence"] = max(result["confidence"], debate.confidence)
            resolved_results.append(result)

        return resolved_results

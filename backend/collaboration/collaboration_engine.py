from __future__ import annotations

from backend.collaboration.conflict_resolver import ConflictResolver
from backend.collaboration.result_aggregator import ResultAggregator
from backend.collaboration.risk_scoring import score_risk_level
from backend.models.reasoning_models import ConsensusIssue, DebateResult


class CollaborationEngine:
    """Coordinate result aggregation, conflict handling, and final issue fusion."""

    def __init__(self) -> None:
        self.result_aggregator = ResultAggregator()
        self.conflict_resolver = ConflictResolver()

    def collaborate(
        self,
        reasoning_outputs: list,
        debates: list[DebateResult],
    ) -> list[ConsensusIssue]:
        aggregated_results = self.result_aggregator.aggregate(reasoning_outputs)
        resolved_results = self.conflict_resolver.resolve(aggregated_results, debates)

        final_issues: list[ConsensusIssue] = []
        for result in resolved_results:
            risk_level = score_risk_level(
                result["severity"],
                result["confidence"],
                len(result.get("verified_by", [])),
            )
            final_issues.append(
                ConsensusIssue(
                    issue=result["issue"],
                    issue_key=result["issue_key"],
                    file_path=result["file_path"],
                    line_number=result["line_number"],
                    severity=result["severity"],
                    confidence=result["confidence"],
                    recommendation=result["recommendation"],
                    detected_by=result["detected_by"],
                    verified_by=result.get("verified_by", []),
                    risk_level=risk_level,
                    status=result["status"],
                    reasoning_chain=result["reasoning_chain"]
                    + [f"Collaboration layer assigned risk level '{risk_level}'."],
                )
            )

        return final_issues

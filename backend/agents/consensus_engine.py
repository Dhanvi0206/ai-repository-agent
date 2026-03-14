from __future__ import annotations

from collections import defaultdict

from backend.models.reasoning_models import (
    AgentReasoningOutput,
    ConsensusIssue,
    DebateResult,
)


class ConsensusEngine:
    """Builds final verified issues from debate outcomes and confidence scores."""

    def build_consensus(
        self,
        reasoning_outputs: list[AgentReasoningOutput],
        debates: list[DebateResult],
    ) -> list[ConsensusIssue]:
        outputs_by_issue: dict[str, list[AgentReasoningOutput]] = defaultdict(list)
        for output in reasoning_outputs:
            outputs_by_issue[_issue_key(output)].append(output)

        consensus_issues: list[ConsensusIssue] = []
        for debate in debates:
            issue_outputs = outputs_by_issue.get(debate.issue_key, [])
            if not issue_outputs:
                continue

            representative = max(issue_outputs, key=lambda output: output.confidence)
            status = _consensus_status(debate)
            consensus_issues.append(
                ConsensusIssue(
                    issue=representative.issue_type,
                    issue_key=debate.issue_key,
                    file_path=representative.file_path,
                    line_number=representative.line_number,
                    severity=representative.severity,
                    confidence=debate.confidence,
                    recommendation=representative.recommendation,
                    verified_by=debate.supporting_agents,
                    status=status,
                    reasoning_chain=_reasoning_chain(representative, debate),
                )
            )

        return consensus_issues


def _consensus_status(debate: DebateResult) -> str:
    if debate.confidence >= 0.85 and debate.status == "accepted":
        return "accepted"
    if debate.confidence >= 0.6:
        return "warning"
    return "discarded"


def _reasoning_chain(reasoning_output: AgentReasoningOutput, debate: DebateResult) -> list[str]:
    chain = [
        f"{reasoning_output.agent} detected pattern '{reasoning_output.issue_type}'.",
        reasoning_output.reasoning,
        debate.outcome,
    ]
    if debate.supporting_agents:
        chain.append(
            "Consensus engine considered support from: "
            + ", ".join(debate.supporting_agents)
            + "."
        )
    return chain


def _issue_key(reasoning_output: AgentReasoningOutput) -> str:
    return (
        f"{reasoning_output.file_path}:{reasoning_output.line_number or 0}:"
        f"{reasoning_output.issue_type}"
    )

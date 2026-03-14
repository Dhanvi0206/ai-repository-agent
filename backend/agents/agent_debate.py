from __future__ import annotations

from collections import defaultdict

from backend.models.reasoning_models import AgentCritique, AgentReasoningOutput, DebateResult


class AgentDebate:
    """Resolves conflicting peer reviews into a debate outcome."""

    def debate(
        self,
        reasoning_outputs: list[AgentReasoningOutput],
        critiques: list[AgentCritique],
    ) -> list[DebateResult]:
        critiques_by_issue: dict[str, list[AgentCritique]] = defaultdict(list)
        for critique in critiques:
            critiques_by_issue[critique.issue_key].append(critique)

        reasoning_by_issue: dict[str, list[AgentReasoningOutput]] = defaultdict(list)
        for output in reasoning_outputs:
            reasoning_by_issue[_issue_key(output)].append(output)

        debate_results: list[DebateResult] = []
        for issue_key, issue_outputs in reasoning_by_issue.items():
            issue_critiques = critiques_by_issue.get(issue_key, [])
            confirmations = [c for c in issue_critiques if c.result == "confirmed"]
            questions = [c for c in issue_critiques if c.result == "questioned"]

            if confirmations and not questions:
                status = "accepted"
                outcome = "Peer agents confirmed the finding."
            elif confirmations and questions:
                status = "warning"
                outcome = "Peer agents produced mixed feedback; manual review recommended."
            elif questions:
                status = "rejected"
                outcome = "Peer agents challenged the finding."
            else:
                status = "warning"
                outcome = "No strong peer evidence available."

            supporting_agents = sorted({output.agent for output in issue_outputs} | {c.critic_agent for c in confirmations})
            opposing_agents = sorted({c.critic_agent for c in questions})
            avg_confidence = sum(output.confidence for output in issue_outputs) / len(issue_outputs)
            if issue_critiques:
                avg_confidence = (avg_confidence + sum(c.confidence for c in issue_critiques) / len(issue_critiques)) / 2

            debate_results.append(
                DebateResult(
                    issue_key=issue_key,
                    status=status,
                    outcome=outcome,
                    supporting_agents=supporting_agents,
                    opposing_agents=opposing_agents,
                    confidence=round(avg_confidence, 2),
                )
            )

        return debate_results


def resolve_agent_conflicts(
    results: list[AgentReasoningOutput],
    critiques: list[AgentCritique],
) -> list[DebateResult]:
    """Compatibility helper matching the Phase spec."""
    return AgentDebate().debate(results, critiques)


def _issue_key(reasoning_output: AgentReasoningOutput) -> str:
    return (
        f"{reasoning_output.file_path}:{reasoning_output.line_number or 0}:"
        f"{reasoning_output.issue_type}"
    )

from __future__ import annotations

from backend.models.reasoning_models import AgentCritique, AgentReasoningOutput


class AgentCritic:
    """Runs peer review across agent reasoning outputs."""

    def critique(
        self,
        reasoning_outputs: list[AgentReasoningOutput],
    ) -> list[AgentCritique]:
        critiques: list[AgentCritique] = []

        for target in reasoning_outputs:
            issue_key = _issue_key(target)
            peer_outputs = [
                output
                for output in reasoning_outputs
                if output.agent != target.agent and _issue_key(output) == issue_key
            ]

            if not peer_outputs:
                critiques.append(
                    AgentCritique(
                        critic_agent="peer_review_router",
                        target_agent=target.agent,
                        issue_key=issue_key,
                        result="not_applicable",
                        confidence=0.0,
                        notes="No peer agent produced a matching issue for review.",
                    )
                )
                continue

            for peer in peer_outputs:
                validation = "confirmed" if peer.severity == target.severity else "questioned"
                confidence = round((peer.confidence + target.confidence) / 2, 2)
                critiques.append(
                    AgentCritique(
                        critic_agent=peer.agent,
                        target_agent=target.agent,
                        issue_key=issue_key,
                        result=validation,
                        confidence=confidence,
                        notes=(
                            f"{peer.agent} reviewed {target.agent}'s finding "
                            f"for {target.file_path}."
                        ),
                    )
                )

        return critiques


def critique_agent_results(
    agent_results: list[AgentReasoningOutput],
) -> list[AgentCritique]:
    """Compatibility helper matching the Phase spec."""
    return AgentCritic().critique(agent_results)


def _issue_key(reasoning_output: AgentReasoningOutput) -> str:
    return (
        f"{reasoning_output.file_path}:{reasoning_output.line_number or 0}:"
        f"{reasoning_output.issue_type}"
    )

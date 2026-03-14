from __future__ import annotations

from backend.models.reasoning_models import AgentReasoningOutput
from backend.models.response_models import AgentResponse


def build_reasoning_outputs(agent_results: list[AgentResponse]) -> list[AgentReasoningOutput]:
    """Normalize raw agent issues into explicit reasoning records."""
    reasoning_outputs: list[AgentReasoningOutput] = []

    for result in agent_results:
        for issue in result.issues:
            reasoning_outputs.append(
                AgentReasoningOutput(
                    agent=result.agent_name,
                    issue_type=issue.issue_type,
                    file_path=issue.file_path,
                    line_number=issue.line_number,
                    analysis=issue.description,
                    reasoning=issue.reasoning
                    or (
                        f"{result.agent_name} detected '{issue.issue_type}' in "
                        f"{issue.file_path} based on repository context and code pattern analysis."
                    ),
                    severity=issue.severity,
                    recommendation=issue.recommendation,
                    confidence=issue.confidence_score,
                )
            )

    return reasoning_outputs

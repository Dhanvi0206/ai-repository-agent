from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.models.reasoning_models import AgentReasoningOutput
from backend.models.response_models import AgentIssue, AgentResponse


class BaseAgent(ABC):
    """Standard interface implemented by every analysis agent."""

    agent_name: str

    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name
        self._issues: list[AgentIssue] = []
        self.repository_context: dict[str, Any] = {}

    @abstractmethod
    def analyze_code(self, files: list[dict[str, Any]]) -> list[AgentIssue]:
        """Inspect repository files and return standardized issues."""

    @abstractmethod
    def generate_report(self) -> str:
        """Return a concise agent-specific summary for logs or reporting."""

    def return_standard_response(self) -> AgentResponse:
        """Wrap collected issues in the shared orchestrator response schema."""
        return AgentResponse(agent_name=self.agent_name, issues=self._issues)

    def analyze(
        self,
        files: list[dict[str, Any]],
        repository_context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """Common orchestration entrypoint used by the backend orchestrator."""
        self.repository_context = repository_context or {}
        self._issues = self.analyze_code(files)
        return self.return_standard_response()

    def build_reasoning_output(self, response: AgentResponse) -> list[AgentReasoningOutput]:
        """Convert issue findings into structured reasoning output."""
        return [
            AgentReasoningOutput(
                agent=self.agent_name,
                issue_type=issue.issue_type,
                file_path=issue.file_path,
                line_number=issue.line_number,
                analysis=issue.description,
                reasoning=issue.reasoning
                or (
                    f"{self.agent_name} identified {issue.issue_type} in {issue.file_path} "
                    "using the repository context and chunk evidence."
                ),
                severity=issue.severity,
                recommendation=issue.recommendation,
                confidence=issue.confidence_score,
            )
            for issue in response.issues
        ]

    def create_issue(
        self,
        *,
        file_path: str,
        issue_type: str,
        description: str,
        reasoning: str,
        recommendation: str,
        severity: str = "medium",
        confidence_score: float = 0.75,
        line_number: int | None = None,
    ) -> AgentIssue:
        return AgentIssue(
            file_path=file_path,
            line_number=line_number,
            issue_type=issue_type,
            severity=severity,
            description=description,
            reasoning=reasoning,
            recommendation=recommendation,
            confidence_score=confidence_score,
        )

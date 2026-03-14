from __future__ import annotations

from backend.agents.base_agent import BaseAgent
from backend.models.response_models import AgentIssue


class LearningAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("learning_agent")

    def analyze_code(self, files: list[dict]) -> list[AgentIssue]:
        issues: list[AgentIssue] = []
        knowledge_context = self.repository_context.get("knowledge_context", {})

        if knowledge_context.get("similar_repository"):
            issues.append(
                self.create_issue(
                    file_path="repository",
                    issue_type="Known Repository Pattern",
                    severity="low",
                    description=(
                        "Repository appears similar to previously analyzed projects."
                    ),
                    reasoning=(
                        "The knowledge system matched this repository profile to prior analyses "
                        "and suggested historically useful checks."
                    ),
                    recommendation=(
                        "Prioritize checks for: "
                        + ", ".join(knowledge_context.get("recommended_checks", []))
                    ),
                    confidence_score=max(0.6, knowledge_context.get("similarity_score", 0.0)),
                )
            )

        return issues

    def generate_report(self) -> str:
        return "Learning agent uses repository knowledge and similarity hints from prior analyses."

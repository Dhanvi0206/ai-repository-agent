from __future__ import annotations

import re

from backend.agents.base_agent import BaseAgent
from backend.models.response_models import AgentIssue


class CodeQualityAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("code_quality_agent")

    def analyze_code(self, files: list[dict]) -> list[AgentIssue]:
        issues: list[AgentIssue] = []

        for chunk in files:
            content = chunk.get("chunk", "")
            control_flow_count = len(re.findall(r"\b(if|for|while|elif|case|except)\b", content))
            if control_flow_count >= 12:
                issues.append(
                    self.create_issue(
                        file_path=chunk["file"],
                        line_number=chunk.get("start_line"),
                        issue_type="High Complexity",
                        severity="medium",
                        description="Chunk contains many branching or looping statements.",
                        reasoning="High branching density is a useful proxy for elevated complexity and lower maintainability.",
                        recommendation="Reduce nesting and split complex logic into smaller helper functions.",
                        confidence_score=0.79,
                    )
                )

            if re.search(r"\b[a-zA-Z]\s*=\s*", content):
                issues.append(
                    self.create_issue(
                        file_path=chunk["file"],
                        issue_type="Weak Variable Naming",
                        severity="low",
                        description="Single-letter variable assignments detected.",
                        reasoning="Non-descriptive variable names reduce code clarity and maintainability.",
                        recommendation="Rename temporary variables to communicate intent more clearly.",
                        confidence_score=0.62,
                    )
                )

        return issues

    def generate_report(self) -> str:
        return "Code quality agent checks complexity signals and naming quality."

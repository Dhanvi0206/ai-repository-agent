from __future__ import annotations

import re

from backend.agents.base_agent import BaseAgent
from backend.models.response_models import AgentIssue


class DocumentationAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("documentation_agent")

    def analyze_code(self, files: list[dict]) -> list[AgentIssue]:
        issues: list[AgentIssue] = []
        metadata = self.repository_context.get("metadata", {})

        if not metadata.get("has_readme"):
            issues.append(
                self.create_issue(
                    file_path="README.md",
                    issue_type="Missing README",
                    severity="medium",
                    description="Repository does not appear to contain a README file.",
                    reasoning="Projects without a README are harder to onboard, review, and maintain.",
                    recommendation="Add a README with setup steps, architecture notes, and usage examples.",
                    confidence_score=0.95,
                )
            )

        for chunk in files:
            if chunk.get("language") != "python":
                continue
            content = chunk.get("chunk", "")
            if re.search(r"^\s*def\s+\w+\(", content, re.MULTILINE) and '"""' not in content and "'''" not in content:
                issues.append(
                    self.create_issue(
                        file_path=chunk["file"],
                        line_number=chunk.get("start_line"),
                        issue_type="Missing Docstring",
                        severity="low",
                        description="Python function block appears to be undocumented.",
                        reasoning="Docstrings improve code readability and downstream agent understanding.",
                        recommendation="Add a concise docstring describing purpose, inputs, and outputs.",
                        confidence_score=0.74,
                    )
                )

        return issues

    def generate_report(self) -> str:
        return "Documentation agent identifies missing README content and Python docstrings."

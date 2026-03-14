from __future__ import annotations

from collections import Counter

from backend.agents.base_agent import BaseAgent
from backend.models.response_models import AgentIssue


class CodeReviewAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("code_review_agent")

    def analyze_code(self, files: list[dict]) -> list[AgentIssue]:
        issues: list[AgentIssue] = []
        file_chunks = self._group_chunks_by_file(files)

        for file_path, chunks in file_chunks.items():
            total_lines = max(chunk.get("end_line", 0) for chunk in chunks)
            if total_lines > 100:
                issues.append(
                    self.create_issue(
                        file_path=file_path,
                        line_number=1,
                        issue_type="Long Function",
                        severity="medium",
                        description="Function or file section exceeds recommended length.",
                        reasoning="Large code blocks are harder to review, test, and maintain.",
                        recommendation="Refactor the logic into smaller, focused functions.",
                        confidence_score=0.81,
                    )
                )

            snippet_counter = Counter(chunk["chunk"][:120].strip() for chunk in chunks if chunk["chunk"].strip())
            duplicated_snippets = [snippet for snippet, count in snippet_counter.items() if count > 1]
            if duplicated_snippets:
                issues.append(
                    self.create_issue(
                        file_path=file_path,
                        issue_type="Duplicate Logic",
                        severity="medium",
                        description="Repeated code patterns detected across multiple chunks.",
                        reasoning="Duplicated logic often increases maintenance cost and bug risk.",
                        recommendation="Extract the repeated logic into a shared helper or utility.",
                        confidence_score=0.73,
                    )
                )

        return issues

    def generate_report(self) -> str:
        return "Code review agent checks for oversized functions and repeated logic."

    def _group_chunks_by_file(self, files: list[dict]) -> dict[str, list[dict]]:
        grouped: dict[str, list[dict]] = {}
        for chunk in files:
            grouped.setdefault(chunk["file"], []).append(chunk)
        return grouped

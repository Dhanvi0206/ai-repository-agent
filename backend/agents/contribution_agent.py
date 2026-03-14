from __future__ import annotations

from pathlib import Path
import subprocess

from backend.agents.base_agent import BaseAgent
from backend.models.response_models import AgentIssue


class ContributionAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("contribution_intelligence_agent")

    def analyze_code(self, files: list[dict]) -> list[AgentIssue]:
        repo_path = self.repository_context.get("local_path")
        if not repo_path or not Path(repo_path).exists():
            return []

        author_counts = self._collect_author_counts(Path(repo_path))
        if not author_counts:
            return []

        top_author, commit_count = max(author_counts.items(), key=lambda item: item[1])
        total_commits = sum(author_counts.values())
        reputation_score = round(min(0.4 + (commit_count / max(total_commits, 1)), 0.99), 2)

        return [
            self.create_issue(
                file_path="repository",
                issue_type="Contributor Reputation Signal",
                severity="low",
                description=f"Top contributor {top_author} has a reputation score of {reputation_score}.",
                reasoning="Recent commit concentration can be used as a lightweight signal for repository ownership and familiarity.",
                recommendation="Use contributor ownership signals when routing reviews and assigning follow-up actions.",
                confidence_score=reputation_score,
            )
        ]

    def generate_report(self) -> str:
        return "Contribution agent derives lightweight contributor reputation signals from git history."

    def _collect_author_counts(self, repo_path: Path) -> dict[str, int]:
        command = [
            "git",
            "-c",
            "safe.directory=*",
            "-C",
            str(repo_path),
            "log",
            "--format=%an",
            "-n",
            "25",
        ]
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return {}

        author_counts: dict[str, int] = {}
        for line in result.stdout.splitlines():
            author = line.strip() or "unknown"
            author_counts[author] = author_counts.get(author, 0) + 1
        return author_counts

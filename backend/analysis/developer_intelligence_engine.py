from __future__ import annotations

import subprocess
from pathlib import Path


class DeveloperIntelligenceEngine:
    """Analyze local git history and produce developer behavior insights."""

    def generate_insights(self, repository_report: dict, repository_metadata: dict) -> dict:
        local_path = repository_metadata.get("local_path")
        contributors = self._collect_contributor_stats(local_path) if local_path else {}
        repository_scores = repository_report.get("repository_scores", {})
        total_issues = repository_report.get("total_issues", 0)
        top_level_report = repository_report.get("developer_intelligence", {}).get(
            "developer_insights",
            [],
        )
        baseline_quality = (repository_scores.get("code_quality_score") or 70.0) / 100

        if not contributors:
            fallback = top_level_report[0] if top_level_report else {
                "developer": "unknown",
                "reputation_score": 0.5,
                "pr_acceptance_rate": 0.75,
                "bug_frequency": 0.0,
            }
            return {
                "developer_insights": [
                    {
                        **fallback,
                        "insight": "Contributor intelligence is limited because repository commit history is unavailable.",
                        "improvement_suggestion": "Enable git history access to improve developer analytics.",
                    }
                ],
                "leaderboard": [fallback["developer"]],
                "risk_contributors": [],
                "developer_activity": {
                    fallback["developer"]: 0,
                },
            }

        total_commits = sum(item["commits"] for item in contributors.values())
        insights = []
        risk_contributors = []

        for developer, stats in sorted(
            contributors.items(),
            key=lambda item: item[1]["commits"],
            reverse=True,
        ):
            commits = stats["commits"]
            commit_frequency = round(commits / max(total_commits, 1), 2)
            bug_frequency = round(min((total_issues / max(total_commits, 1)) * (1.2 - commit_frequency), 1.0), 2)
            pr_acceptance_rate = round(max(0.55, min(0.98, 0.95 - (bug_frequency * 0.25))), 2)
            code_quality_score = round(max(0.45, min(0.98, baseline_quality + (commit_frequency * 0.2))), 2)
            reputation_score = round(
                (pr_acceptance_rate * 0.4)
                + (code_quality_score * 0.3)
                + ((1 - bug_frequency) * 0.2)
                + (commit_frequency * 0.1),
                2,
            )

            insight = self._build_insight(commits, bug_frequency, reputation_score)
            suggestion = self._build_suggestion(bug_frequency, reputation_score, commit_frequency)
            entry = {
                "developer": developer,
                "commits": commits,
                "commit_frequency": commit_frequency,
                "pr_acceptance_rate": pr_acceptance_rate,
                "bug_frequency": bug_frequency,
                "code_quality_score": code_quality_score,
                "reputation_score": reputation_score,
                "insight": insight,
                "improvement_suggestion": suggestion,
            }
            insights.append(entry)
            if bug_frequency >= 0.45 or reputation_score < 0.65:
                risk_contributors.append(
                    {
                        "developer": developer,
                        "risk_flag": "high_bug_rate" if bug_frequency >= 0.45 else "low_reputation_score",
                        "reason": insight,
                    }
                )

        return {
            "developer_insights": insights,
            "leaderboard": [entry["developer"] for entry in insights[:5]],
            "risk_contributors": risk_contributors,
            "developer_activity": {
                developer: stats["commits"]
                for developer, stats in sorted(
                    contributors.items(),
                    key=lambda item: item[1]["commits"],
                    reverse=True,
                )
            },
        }

    def _collect_contributor_stats(self, local_path: str) -> dict[str, dict]:
        repo_path = Path(local_path)
        if not repo_path.exists():
            return {}

        command = [
            "git",
            "-c",
            "safe.directory=*",
            "-C",
            str(repo_path),
            "log",
            "--format=%an",
            "-n",
            "100",
        ]
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return {}

        contributors: dict[str, dict] = {}
        for line in result.stdout.splitlines():
            developer = line.strip() or "unknown"
            contributors.setdefault(developer, {"commits": 0})
            contributors[developer]["commits"] += 1
        return contributors

    def _build_insight(self, commits: int, bug_frequency: float, reputation_score: float) -> str:
        if reputation_score >= 0.8 and bug_frequency < 0.2:
            return "High quality commits with strong delivery reliability."
        if commits >= 15 and bug_frequency < 0.35:
            return "Frequent contributor with generally stable changes."
        if bug_frequency >= 0.45:
            return "Frequent commits but higher bug introduction risk."
        return "Moderate contribution quality with room to improve consistency."

    def _build_suggestion(
        self,
        bug_frequency: float,
        reputation_score: float,
        commit_frequency: float,
    ) -> str:
        if bug_frequency >= 0.45:
            return "Review testing practices and strengthen code review before merging."
        if reputation_score < 0.65:
            return "Focus on smaller, well-tested changes to improve reliability."
        if commit_frequency < 0.1:
            return "Increase contribution consistency to build stronger repository familiarity."
        return "Continue current contribution patterns and mentor others on review quality."

from __future__ import annotations


class DevOpsDashboardEngine:
    """Build a consolidated DevOps dashboard payload from analysis outputs."""

    def build_dashboard(
        self,
        repository_report: dict,
        repository_summary: dict,
        agent_status: dict | None,
        developer_intelligence: dict,
        risk_heatmap: dict,
        risk_predictions: dict,
        technical_debt: dict,
    ) -> dict:
        high_risk_files = [
            entry["file"]
            for entry in risk_heatmap.get("risk_heatmap", [])
            if entry.get("risk_level") == "high"
        ][:5]
        dependency_issues = repository_report.get("dependency_risk_report", {}).get(
            "dependency_risks",
            [],
        )
        top_contributors = [
            {
                "developer": item.get("developer"),
                "reputation_score": item.get("reputation_score"),
            }
            for item in developer_intelligence.get("developer_insights", [])[:5]
        ]
        agent_activity = []
        execution_timeline = []
        if agent_status:
            agent_activity = [
                f"{self._format_agent_name(item['agent'])}: {item['message']}"
                for item in agent_status.get("agent_execution_status", [])
            ]
            execution_timeline = agent_status.get("execution_timeline", [])

        alerts = self._build_alerts(repository_report, risk_predictions, risk_heatmap)

        return {
            "repository_overview": {
                "repository_name": repository_report.get("repository"),
                "primary_language": repository_summary.get("repository_overview", {}).get(
                    "primary_language"
                ),
                "total_files": repository_report.get("total_issues", 0),
                "repo_health_score": repository_report.get("repo_health_score"),
                "repository_type": repository_summary.get("repository_overview", {}).get(
                    "type"
                ),
            },
            "agent_activity": agent_activity,
            "security_analysis": {
                "security_score": repository_report.get("security_score"),
                "critical_vulnerabilities": repository_report.get("critical_issues", 0),
                "high_risk_files": high_risk_files,
            },
            "code_quality": {
                "quality_score": repository_report.get("code_quality_score"),
                "code_smells": len(
                    repository_report.get("code_quality_report", {}).get(
                        "code_quality_issues",
                        []
                    )
                ),
                "high_complexity_functions": sum(
                    1
                    for issue in repository_report.get("issues", [])
                    if issue.get("issue") == "High Complexity"
                ),
                "technical_debt_score": technical_debt.get("technical_debt_score"),
            },
            "dependency_risk": {
                "dependency_score": repository_report.get("dependency_score"),
                "outdated_packages": len(dependency_issues),
                "vulnerable_dependencies": len(dependency_issues),
            },
            "developer_insights": {
                "top_contributors": top_contributors,
                "leaderboard": developer_intelligence.get("leaderboard", []),
                "risk_contributors": developer_intelligence.get("risk_contributors", []),
            },
            "chart_data": {
                "security": repository_report.get("security_score"),
                "quality": repository_report.get("code_quality_score"),
                "documentation": repository_report.get("documentation_score"),
                "dependency": repository_report.get("dependency_score"),
                "technical_debt": technical_debt.get("technical_debt_score"),
            },
            "agent_execution_timeline": execution_timeline,
            "alerts": alerts,
            "visualizations": {
                "risk_heatmap": risk_heatmap.get("visual_risk_data", {}),
                "risk_predictions": risk_predictions.get("risk_probabilities", {}),
            },
        }

    def _format_agent_name(self, agent_name: str) -> str:
        return agent_name.replace("_", " ").title()

    def _build_alerts(
        self,
        repository_report: dict,
        risk_predictions: dict,
        risk_heatmap: dict,
    ) -> list[str]:
        alerts: list[str] = []
        if repository_report.get("critical_issues", 0) > 0:
            alerts.append("Critical vulnerability detected. Immediate remediation is recommended.")
        top_risky_file = next(
            (
                entry["file"]
                for entry in risk_heatmap.get("risk_heatmap", [])
                if entry.get("risk_level") == "high"
            ),
            None,
        )
        if top_risky_file:
            alerts.append(f"High-risk file detected: {top_risky_file}")
        warning = risk_predictions.get("high_impact_warning")
        if warning:
            alerts.append(warning)
        return alerts[:5]

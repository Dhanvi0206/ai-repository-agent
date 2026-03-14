from __future__ import annotations

from backend.reporting.explanation_builder import build_explanation
from backend.reporting.fix_suggestion_engine import build_fix_suggestion
from backend.reporting.risk_prioritizer import prioritize_issues


class ReportingAgent:
    """Aggregates multi-agent outputs into a final repository intelligence report."""

    HEALTH_WEIGHTS = {
        "security_score": 0.4,
        "code_quality_score": 0.3,
        "documentation_score": 0.15,
        "dependency_score": 0.15,
    }

    def generate_report(self, analysis_response) -> dict:
        prioritized = prioritize_issues(analysis_response.analysis.consensus_issues)
        learned_suggestions = analysis_response.analysis.knowledge_insights.get(
            "fix_suggestions",
            [],
        )

        issues = [self._build_issue_entry(issue, learned_suggestions) for issue in prioritized["issues"]]
        report = {
            "repository": analysis_response.repository.repository_name,
            "owner": analysis_response.repository.owner,
            "repo_health_score": self._compute_weighted_health(analysis_response.health_score),
            "security_score": analysis_response.health_score.security_score,
            "code_quality_score": analysis_response.health_score.code_quality_score,
            "documentation_score": analysis_response.health_score.documentation_score,
            "dependency_score": analysis_response.health_score.dependency_score,
            "total_issues": len(issues),
            "critical_issues": prioritized["counts"]["critical_issues"],
            "high_issues": prioritized["counts"]["high_issues"],
            "medium_issues": prioritized["counts"]["medium_issues"],
            "low_issues": prioritized["counts"]["low_issues"],
            "security_report": self._build_security_report(issues),
            "code_quality_report": self._build_code_quality_report(issues),
            "dependency_risk_report": self._build_dependency_report(issues),
            "documentation_report": self._build_documentation_report(issues),
            "developer_intelligence": self._build_developer_intelligence(analysis_response),
            "risk_distribution": prioritized["counts"],
            "chart_data": {
                "security_score": analysis_response.health_score.security_score,
                "quality_score": analysis_response.health_score.code_quality_score,
                "docs_score": analysis_response.health_score.documentation_score,
                "dependency_score": analysis_response.health_score.dependency_score,
            },
            "summary": self._build_executive_summary(analysis_response, prioritized["counts"]),
            "issues": issues,
            "repository_scores": analysis_response.health_score.model_dump(),
            "knowledge_insights": analysis_response.analysis.knowledge_insights,
            "execution_log": analysis_response.analysis.execution_log,
            "export_formats": ["json", "html", "pdf"],
        }
        return report

    def _build_issue_entry(self, issue, learned_suggestions: list[dict]) -> dict:
        return {
            "issue": issue.issue,
            "severity": issue.severity,
            "risk_level": issue.risk_level,
            "file": issue.file_path,
            "line": issue.line_number,
            "reasoning": build_explanation(issue),
            "reasoning_chain": issue.reasoning_chain,
            "fix": build_fix_suggestion(issue, learned_suggestions),
            "confidence": issue.confidence,
            "verified_by": issue.verified_by,
            "detected_by": issue.detected_by,
        }

    def _compute_weighted_health(self, health_score) -> float:
        return round(
            (health_score.security_score or 0) * self.HEALTH_WEIGHTS["security_score"]
            + (health_score.code_quality_score or 0) * self.HEALTH_WEIGHTS["code_quality_score"]
            + (health_score.documentation_score or 0) * self.HEALTH_WEIGHTS["documentation_score"]
            + (health_score.dependency_score or 0) * self.HEALTH_WEIGHTS["dependency_score"],
            2,
        )

    def _build_security_report(self, issues: list[dict]) -> dict:
        return {
            "security_issues": [
                issue
                for issue in issues
                if "security_agent" in issue["detected_by"]
            ]
        }

    def _build_code_quality_report(self, issues: list[dict]) -> dict:
        return {
            "code_quality_issues": [
                issue
                for issue in issues
                if {"code_review_agent", "code_quality_agent"} & set(issue["detected_by"])
            ]
        }

    def _build_dependency_report(self, issues: list[dict]) -> dict:
        dependency_risks = []
        for issue in issues:
            if "dependency_agent" not in issue["detected_by"]:
                continue
            dependency_risks.append(
                {
                    "dependency": issue["file"],
                    "version": None,
                    "vulnerability": issue["issue"],
                    "severity": issue["severity"],
                    "reasoning": issue["reasoning"],
                }
            )
        return {"dependency_risks": dependency_risks}

    def _build_documentation_report(self, issues: list[dict]) -> dict:
        return {
            "documentation_issues": [
                f"{issue['issue']} in {issue['file']}"
                for issue in issues
                if "documentation_agent" in issue["detected_by"]
            ]
        }

    def _build_developer_intelligence(self, analysis_response) -> dict:
        intelligence_summary = analysis_response.health_score.intelligence_summary
        return {
            "developer_insights": [
                {
                    "developer": intelligence_summary.get("top_contributor"),
                    "reputation_score": analysis_response.health_score.developer_reputation_score,
                    "pr_acceptance_rate": intelligence_summary.get("pr_acceptance_rate"),
                    "bug_frequency": intelligence_summary.get("bug_frequency"),
                }
            ]
        }

    def _build_executive_summary(self, analysis_response, risk_counts: dict) -> str:
        repo_name = analysis_response.repository.repository_name or "Repository"
        security_score = analysis_response.health_score.security_score or 0
        docs_score = analysis_response.health_score.documentation_score or 0
        if risk_counts["critical_issues"] > 0:
            risk_statement = "has critical risks that should be addressed immediately"
        elif risk_counts["high_issues"] > 0:
            risk_statement = "has moderate to high risks that should be prioritized"
        else:
            risk_statement = "appears relatively stable with mostly manageable issues"

        docs_statement = (
            "good documentation quality"
            if docs_score >= 80
            else "documentation gaps that need attention"
        )
        return (
            f"{repo_name} {risk_statement}. "
            f"Security score is {security_score:.0f} and the repository shows {docs_statement}. "
            "Main issues are highlighted below with reasoning and actionable fixes."
        )

from __future__ import annotations


class RiskPredictionEngine:
    """Generate simple forward-looking repository risk predictions."""

    def predict(self, repository_report: dict) -> dict:
        security_issues = repository_report.get("security_report", {}).get(
            "security_issues",
            [],
        )
        dependency_risks = repository_report.get("dependency_risk_report", {}).get(
            "dependency_risks",
            [],
        )
        quality_issues = repository_report.get("code_quality_report", {}).get(
            "code_quality_issues",
            [],
        )
        documentation_issues = repository_report.get("documentation_report", {}).get(
            "documentation_issues",
            [],
        )
        knowledge_metrics = repository_report.get("knowledge_insights", {}).get(
            "knowledge_metrics",
            {},
        )
        repository_scores = repository_report.get("repository_scores", {})

        predictions: list[dict] = []

        if len(security_issues) >= 2 or repository_scores.get("security_score", 100) < 80:
            predictions.append(
                {
                    "risk_type": "security",
                    "prediction": "Security risk may increase if current insecure patterns remain unresolved.",
                    "reason": self._security_reason(security_issues, knowledge_metrics),
                    "probability": self._bounded_probability(
                        0.45 + (len(security_issues) * 0.1),
                    ),
                    "trend": "increasing",
                }
            )

        if len(dependency_risks) >= 2 or repository_scores.get("dependency_score", 100) < 85:
            predictions.append(
                {
                    "risk_type": "dependency",
                    "prediction": "Dependency risk is likely to escalate if outdated packages are not updated.",
                    "reason": self._dependency_reason(dependency_risks),
                    "probability": self._bounded_probability(
                        0.4 + (len(dependency_risks) * 0.12),
                    ),
                    "trend": "increasing",
                }
            )

        if len(quality_issues) >= 3 or repository_scores.get("code_quality_score", 100) < 75:
            predictions.append(
                {
                    "risk_type": "code_quality",
                    "prediction": "Maintainability risk may grow as complexity and refactoring debt accumulate.",
                    "reason": self._quality_reason(quality_issues, knowledge_metrics),
                    "probability": self._bounded_probability(
                        0.35 + (len(quality_issues) * 0.08),
                    ),
                    "trend": "increasing",
                }
            )

        if documentation_issues or repository_scores.get("documentation_score", 100) < 80:
            predictions.append(
                {
                    "risk_type": "documentation",
                    "prediction": "Documentation quality may degrade onboarding speed and issue resolution over time.",
                    "reason": self._documentation_reason(documentation_issues),
                    "probability": self._bounded_probability(
                        0.25 + (len(documentation_issues) * 0.1),
                    ),
                    "trend": "stable" if len(documentation_issues) <= 1 else "increasing",
                }
            )

        if not predictions:
            predictions.append(
                {
                    "risk_type": "repository",
                    "prediction": "No strong near-term risk escalation signals were detected.",
                    "reason": "Current repository scores and issue counts do not indicate significant worsening trends.",
                    "probability": 0.18,
                    "trend": "stable",
                }
            )

        top_prediction = max(predictions, key=lambda item: item["probability"])
        return {
            "repository": repository_report.get("repository"),
            "current_repo_health_score": repository_report.get("repo_health_score"),
            "risk_predictions": predictions,
            "risk_probabilities": {
                f"{prediction['risk_type']}_risk_probability": prediction["probability"]
                for prediction in predictions
            },
            "risk_trends": {
                prediction["risk_type"]: prediction["trend"] for prediction in predictions
            },
            "high_impact_warning": (
                f"This repository may face severe {top_prediction['risk_type']} risks if "
                f"the current issues are ignored."
                if top_prediction["probability"] >= 0.65
                else "No immediate high-impact escalation warning was triggered."
            ),
        }

    def _security_reason(self, security_issues: list[dict], knowledge_metrics: dict) -> str:
        if security_issues:
            top_issue = security_issues[0]
            return (
                f"{top_issue['issue']} was detected in {top_issue['file']}, and repeated "
                "security findings usually increase future exposure risk."
            )
        common_vulnerability = knowledge_metrics.get("most_common_vulnerability")
        if common_vulnerability:
            return (
                f"Historical analyses frequently surface {common_vulnerability}, which increases "
                "the chance of similar future vulnerabilities."
            )
        return "Existing repository patterns indicate elevated security uncertainty."

    def _dependency_reason(self, dependency_risks: list[dict]) -> str:
        if dependency_risks:
            top_issue = dependency_risks[0]
            return (
                f"{top_issue['vulnerability']} was reported for {top_issue['dependency']}, "
                "suggesting the dependency surface needs attention."
            )
        return "Dependency-related findings suggest future library risk if upgrades are delayed."

    def _quality_reason(self, quality_issues: list[dict], knowledge_metrics: dict) -> str:
        if quality_issues:
            top_issue = quality_issues[0]
            return (
                f"{top_issue['issue']} in {top_issue['file']} indicates maintainability debt "
                "that can compound in future changes."
            )
        common_smell = knowledge_metrics.get("most_common_code_smell")
        if common_smell:
            return (
                f"Historical analyses repeatedly found {common_smell}, suggesting code quality "
                "may continue to decline without refactoring."
            )
        return "Current code patterns indicate possible future maintainability pressure."

    def _documentation_reason(self, documentation_issues: list[str]) -> str:
        if documentation_issues:
            return (
                f"{documentation_issues[0]} was found, which can slow onboarding and future debugging."
            )
        return "Documentation gaps may emerge if current coverage is not maintained."

    def _bounded_probability(self, value: float) -> float:
        return round(max(0.05, min(value, 0.95)), 2)

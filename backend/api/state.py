from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import WebSocket

from backend.analysis.codebase_summary_engine import CodebaseSummaryEngine
from backend.analysis.developer_intelligence_engine import DeveloperIntelligenceEngine
from backend.analysis.fix_priority_engine import FixPriorityEngine
from backend.analysis.risk_heatmap_engine import RiskHeatmapEngine
from backend.analysis.technical_debt_engine import TechnicalDebtEngine
from backend.comparison.repository_comparison_engine import RepositoryComparisonEngine
from backend.dashboard.devops_dashboard_engine import DevOpsDashboardEngine
from backend.learning.knowledge_learning_engine import KnowledgeLearningEngine
from backend.monitoring.agent_execution_monitor import AgentExecutionMonitor
from backend.orchestrator.orchestrator import RepositoryOrchestrator
from backend.prediction.risk_prediction_engine import RiskPredictionEngine
from backend.reporting.dashboard_data_api import (
    build_developer_report,
    build_issue_details,
    build_repository_report,
)
from backend.reporting.explainable_score_engine import ExplainableScoreEngine
from backend.repository.repo_fetcher import RepositoryFetchError
from backend.repository.repo_parser import InvalidGitHubUrlError
from backend.stability.cache_manager import CacheManager
from backend.stability.error_handler import AppError, format_error_response
from backend.stability.logging_system import log_event
from backend.stability.validation import RateLimiter, validate_pagination, validate_repo_url


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def success_response(data: dict) -> dict:
    return {"status": "success", "data": data, "timestamp": utc_now_iso()}


def error_response(message: str, *, code: str = "error", details: dict | None = None) -> dict:
    error = AppError(message=message, error_type=code, details=details)
    return format_error_response(error)


class WebSocketManager:
    def __init__(self) -> None:
        self.connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.connections.discard(websocket)

    async def broadcast(self, event: dict) -> None:
        stale_connections: list[WebSocket] = []
        for connection in self.connections:
            try:
                await connection.send_json(event)
            except Exception:
                stale_connections.append(connection)
        for connection in stale_connections:
            self.disconnect(connection)


class AnalysisService:
    """In-memory async analysis jobs, cached reports, and dashboard accessors."""

    def __init__(self) -> None:
        self.orchestrator = RepositoryOrchestrator()
        self.codebase_summary_engine = CodebaseSummaryEngine()
        self.developer_intelligence_engine = DeveloperIntelligenceEngine()
        self.fix_priority_engine = FixPriorityEngine()
        self.knowledge_learning_engine = KnowledgeLearningEngine()
        self.dashboard_engine = DevOpsDashboardEngine()
        self.risk_heatmap_engine = RiskHeatmapEngine()
        self.technical_debt_engine = TechnicalDebtEngine()
        self.repository_comparison_engine = RepositoryComparisonEngine()
        self.explainable_score_engine = ExplainableScoreEngine()
        self.risk_prediction_engine = RiskPredictionEngine()
        self.jobs: dict[str, dict] = {}
        self.cache = CacheManager(ttl_minutes=30)
        self.repository_index: dict[str, str] = {}
        self.websocket_manager = WebSocketManager()
        self.rate_limiter = RateLimiter(max_requests=10, period_seconds=60)
        self.execution_monitor = AgentExecutionMonitor()

    def _repository_id_from_url(self, repo_url: str) -> str:
        normalized = repo_url.rstrip("/").removesuffix(".git")
        parts = normalized.split("/")
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
        return normalized

    def get_cached_report(self, repository_id: str) -> dict | None:
        cached = self.cache.get(repository_id)
        if not cached:
            return None
        return cached["report"]

    async def run_analysis_job(self, job_id: str, repo_url: str) -> None:
        repository_id = self._repository_id_from_url(repo_url)
        self.jobs[job_id].update({"status": "processing", "repository": repository_id})
        scheduled_agents = self.orchestrator.pipeline_manager.sort_agents(self.orchestrator.agents)
        self.execution_monitor.initialize_job(
            job_id,
            repository_id,
            [agent.agent_name for agent in scheduled_agents],
        )
        self.execution_monitor.record_system_event(
            job_id,
            "repository_fetch_started",
            "Repository analysis started and repository fetch is in progress.",
        )
        log_event("analysis_service", "START", "Analysis job started", job_id=job_id, repository=repository_id)
        await self.websocket_manager.broadcast(
            {"job_id": job_id, "repository": repository_id, "event": "analysis_started"}
        )

        try:
            def progress_callback(event: dict) -> None:
                agent_name = event.get("agent", "unknown_agent")
                status = event.get("status", "running")
                message = event.get("message", "")
                self.execution_monitor.update_agent(
                    job_id,
                    agent_name,
                    status,
                    message,
                    execution_time=event.get("execution_time"),
                    files_analyzed=event.get("files_analyzed"),
                )
                asyncio.run(
                    self.websocket_manager.broadcast(
                        {
                            "job_id": job_id,
                            "repository": repository_id,
                            "event": "agent_status",
                            **event,
                        }
                    )
                )

            await self.websocket_manager.broadcast(
                {"job_id": job_id, "repository": repository_id, "event": "Security Agent started"}
            )
            analysis_response = await asyncio.to_thread(
                self.orchestrator.analyze_repository,
                repo_url,
                progress_callback,
            )
            self.execution_monitor.record_system_event(
                job_id,
                "repository_analysis_completed",
                "Repository analysis pipeline completed successfully.",
            )
            report = build_repository_report(analysis_response)
            self.knowledge_learning_engine.learn_from_report(repository_id, report)
            developer_report = build_developer_report(analysis_response)
            dependency_report = self._build_dependency_report(report)

            self.cache.set(repository_id, {
                "report": report,
                "developer_report": developer_report,
                "dependency_report": dependency_report,
                "raw_response": analysis_response,
            })
            self.repository_index[repository_id] = repo_url
            self.jobs[job_id].update(
                {
                    "status": "completed",
                    "repository": repository_id,
                    "completed_at": utc_now_iso(),
                }
            )
            log_event("analysis_service", "COMPLETE", "Analysis job completed", job_id=job_id, repository=repository_id)
            await self.websocket_manager.broadcast(
                {"job_id": job_id, "repository": repository_id, "event": "analysis_completed"}
            )
        except (InvalidGitHubUrlError, RepositoryFetchError) as exc:
            self.execution_monitor.record_system_event(
                job_id,
                "analysis_failed",
                str(exc),
            )
            self.jobs[job_id].update(
                {
                    "status": "failed",
                    "repository": repository_id,
                    "error": str(exc),
                    "completed_at": utc_now_iso(),
                }
            )
            log_event("analysis_service", "ERROR", "Analysis job failed", job_id=job_id, repository=repository_id, error=str(exc))
            await self.websocket_manager.broadcast(
                {"job_id": job_id, "repository": repository_id, "event": "analysis_failed", "error": str(exc)}
            )
        except Exception as exc:
            self.execution_monitor.record_system_event(
                job_id,
                "analysis_failed",
                str(exc),
            )
            self.jobs[job_id].update(
                {
                    "status": "failed",
                    "repository": repository_id,
                    "error": str(exc),
                    "completed_at": utc_now_iso(),
                }
            )
            log_event("analysis_service", "ERROR", "Unhandled analysis failure", job_id=job_id, repository=repository_id, error=str(exc))
            await self.websocket_manager.broadcast(
                {"job_id": job_id, "repository": repository_id, "event": "analysis_failed", "error": str(exc)}
            )

    def start_analysis(self, repo_url: str) -> dict:
        normalized_repo_url = validate_repo_url(repo_url)
        self.rate_limiter.check("global_analysis")
        repository_id = self._repository_id_from_url(normalized_repo_url)
        cached = self.get_cached_report(repository_id)
        if cached:
            log_event("analysis_service", "CACHE_HIT", "Returning cached analysis", repository=repository_id)
            return {
                "job_id": None,
                "status": "cached",
                "repository": repository_id,
            }

        job_id = f"analysis_{uuid4().hex[:10]}"
        self.jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "repository": repository_id,
            "created_at": utc_now_iso(),
        }
        asyncio.create_task(self.run_analysis_job(job_id, normalized_repo_url))
        return {"job_id": job_id, "status": "processing", "repository": repository_id}

    def get_job_status(self, job_id: str) -> dict | None:
        return self.jobs.get(job_id)

    def get_agent_status(self, job_id: str) -> dict | None:
        return self.execution_monitor.get_job_status(job_id)

    def _require_report(self, repository_id: str) -> dict:
        report = self.get_cached_report(repository_id)
        if not report:
            raise KeyError("analysis_not_completed")
        return report

    def get_repository_health(self, repository_id: str) -> dict:
        report = self._require_report(repository_id)
        return {
            "repository": repository_id,
            "health_score": report["repository_scores"]["score"],
            "security_score": report["repository_scores"]["security_score"],
            "quality_score": report["repository_scores"]["code_quality_score"],
            "documentation_score": report["repository_scores"]["documentation_score"],
            "dependency_score": report["repository_scores"]["dependency_score"],
        }

    def get_developer_score(self, repository_id: str) -> dict:
        cached = self.cache.get(repository_id)
        if not cached:
            raise KeyError("analysis_not_completed")
        return cached["developer_report"]

    def _build_dependency_report(self, report: dict) -> dict:
        dependency_issues = [
            issue for issue in report["issues"] if "dependency_agent" in issue["detected_by"]
        ]
        return {
            "repository": report["repository"],
            "dependencies_scanned": len(dependency_issues),
            "vulnerable_dependencies": len(dependency_issues),
            "critical_risks": sum(1 for issue in dependency_issues if issue["risk_level"] == "critical"),
            "issues": dependency_issues,
        }

    def get_dependency_risk(self, repository_id: str) -> dict:
        cached = self.cache.get(repository_id)
        if not cached:
            raise KeyError("analysis_not_completed")
        return cached["dependency_report"]

    def get_issues(self, repository_id: str, page: int = 1, limit: int = 20) -> dict:
        page, limit = validate_pagination(page, limit)
        report = self._require_report(repository_id)
        issues = report["issues"]
        start = max(page - 1, 0) * limit
        end = start + limit
        return {
            "repository": repository_id,
            "page": page,
            "limit": limit,
            "total": len(issues),
            "items": issues[start:end],
        }

    def get_repository_report(self, repository_id: str) -> dict:
        return self._require_report(repository_id)

    def get_issue_details(self, repository_id: str, issue_key: str | None = None) -> dict:
        cached = self.cache.get(repository_id)
        if not cached:
            raise KeyError("analysis_not_completed")
        return build_issue_details(cached["raw_response"], issue_key)

    def get_score_explanation(self, repository_id: str) -> dict:
        report = self._require_report(repository_id)
        return self.explainable_score_engine.build_score_explanation(report)

    def get_risk_predictions(self, repository_id: str) -> dict:
        report = self._require_report(repository_id)
        return self.risk_prediction_engine.predict(report)

    def get_repository_summary(self, repository_id: str) -> dict:
        cached = self.cache.get(repository_id)
        if not cached:
            raise KeyError("analysis_not_completed")
        raw_response = cached["raw_response"]
        return self.codebase_summary_engine.generate_summary(
            cached["report"],
            raw_response.repository.model_dump(),
        )

    def get_developer_intelligence(self, repository_id: str) -> dict:
        cached = self.cache.get(repository_id)
        if not cached:
            raise KeyError("analysis_not_completed")
        raw_response = cached["raw_response"]
        return self.developer_intelligence_engine.generate_insights(
            cached["report"],
            raw_response.repository.model_dump(),
        )

    def get_technical_debt(self, repository_id: str) -> dict:
        cached = self.cache.get(repository_id)
        if not cached:
            raise KeyError("analysis_not_completed")
        raw_response = cached["raw_response"]
        return self.technical_debt_engine.analyze(
            cached["report"],
            raw_response.repository.model_dump(),
        )

    def get_risk_heatmap(self, repository_id: str) -> dict:
        cached = self.cache.get(repository_id)
        if not cached:
            raise KeyError("analysis_not_completed")
        raw_response = cached["raw_response"]
        technical_debt = self.technical_debt_engine.analyze(
            cached["report"],
            raw_response.repository.model_dump(),
        )
        return self.risk_heatmap_engine.analyze(
            cached["report"],
            technical_debt,
        )

    def get_priority_fixes(self, repository_id: str) -> dict:
        report = self._require_report(repository_id)
        return self.fix_priority_engine.prioritize(report)

    def get_knowledge_insights(self, repository_id: str | None = None) -> dict:
        if repository_id:
            self._require_report(repository_id)
        return self.knowledge_learning_engine.get_insights()

    def get_dashboard_data(self, repository_id: str) -> dict:
        report = self._require_report(repository_id)
        repository_summary = self.get_repository_summary(repository_id)
        developer_intelligence = self.get_developer_intelligence(repository_id)
        technical_debt = self.get_technical_debt(repository_id)
        risk_heatmap = self.get_risk_heatmap(repository_id)
        risk_predictions = self.get_risk_predictions(repository_id)

        agent_status = None
        for job_id, job in reversed(list(self.jobs.items())):
            if job.get("repository") == repository_id:
                agent_status = self.get_agent_status(job_id)
                if agent_status:
                    break

        return self.dashboard_engine.build_dashboard(
            report,
            repository_summary,
            agent_status,
            developer_intelligence,
            risk_heatmap,
            risk_predictions,
            technical_debt,
        )

    def compare_repositories(self, repo_a_id: str, repo_b_id: str) -> dict:
        repo_a_report = self._require_report(repo_a_id)
        repo_b_report = self._require_report(repo_b_id)
        return self.repository_comparison_engine.compare(
            repo_a_id,
            repo_a_report,
            repo_b_id,
            repo_b_report,
        )


analysis_service = AnalysisService()

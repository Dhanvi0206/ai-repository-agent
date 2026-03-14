from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentExecutionMonitor:
    """Track per-job agent state, timeline events, and performance metrics."""

    def __init__(self) -> None:
        self._jobs: dict[str, dict] = {}
        self._lock = Lock()

    def initialize_job(self, job_id: str, repository: str, agents: list[str]) -> None:
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "repository": repository,
                "agent_execution_status": [
                    {
                        "agent": agent,
                        "status": "pending",
                        "message": "Waiting to start",
                        "execution_time": None,
                        "files_analyzed": 0,
                        "updated_at": _utc_now_iso(),
                    }
                    for agent in agents
                ],
                "execution_timeline": [
                    {
                        "timestamp": _utc_now_iso(),
                        "event": "analysis_initialized",
                        "message": "Monitoring initialized for repository analysis.",
                    }
                ],
            }

    def record_system_event(self, job_id: str, event: str, message: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job["execution_timeline"].append(
                {
                    "timestamp": _utc_now_iso(),
                    "event": event,
                    "message": message,
                }
            )

    def update_agent(
        self,
        job_id: str,
        agent_name: str,
        status: str,
        message: str,
        *,
        execution_time: float | None = None,
        files_analyzed: int | None = None,
    ) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return

            for item in job["agent_execution_status"]:
                if item["agent"] != agent_name:
                    continue
                item["status"] = status
                item["message"] = message
                item["updated_at"] = _utc_now_iso()
                if execution_time is not None:
                    item["execution_time"] = execution_time
                if files_analyzed is not None:
                    item["files_analyzed"] = files_analyzed
                break

            job["execution_timeline"].append(
                {
                    "timestamp": _utc_now_iso(),
                    "event": f"{agent_name}_{status}",
                    "message": message,
                }
            )

    def get_job_status(self, job_id: str) -> dict | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            return deepcopy(job)

from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter


@dataclass
class AgentExecutionRecord:
    agent: str
    status: str
    execution_time: float
    start_offset: float
    finish_offset: float
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class ExecutionLogManager:
    """Tracks agent execution timing and failures for orchestrator observability."""

    def __init__(self) -> None:
        self._pipeline_start = perf_counter()

    def build_record(
        self,
        agent_name: str,
        started_at: float,
        finished_at: float,
        status: str,
        error: str | None = None,
    ) -> AgentExecutionRecord:
        return AgentExecutionRecord(
            agent=agent_name,
            status=status,
            execution_time=round(finished_at - started_at, 4),
            start_offset=round(started_at - self._pipeline_start, 4),
            finish_offset=round(finished_at - self._pipeline_start, 4),
            error=error,
        )

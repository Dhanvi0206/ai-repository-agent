from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DeveloperContributionMetrics(BaseModel):
    developer_id: str
    repository_id: str
    developer_name: str
    commit_frequency: float = Field(..., ge=0.0)
    pr_acceptance_rate: float = Field(..., ge=0.0, le=1.0)
    bug_frequency: float = Field(..., ge=0.0, le=1.0)
    code_quality_score: float = Field(..., ge=0.0, le=100.0)
    documentation_score: float = Field(..., ge=0.0, le=100.0)
    reputation_score: float = Field(..., ge=0.0, le=1.0)
    risk_flag: str | None = None
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentPerformanceMetrics(BaseModel):
    agent_name: str
    repository_id: str
    issues_detected: int = Field(default=0, ge=0)
    execution_time: float = Field(..., ge=0.0)
    accuracy_score: float | None = Field(default=None, ge=0.0, le=1.0)
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

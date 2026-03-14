from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RepositoryDashboardData(BaseModel):
    repository_name: str
    owner: str
    health_score: float = Field(..., ge=0.0, le=100.0)
    total_issues: int = Field(default=0, ge=0)
    critical_issues: int = Field(default=0, ge=0)
    high_issues: int = Field(default=0, ge=0)
    top_contributor: str | None = None
    last_analysis_time: datetime | None = None


class IssueSeverityBreakdown(BaseModel):
    critical: int = Field(default=0, ge=0)
    high: int = Field(default=0, ge=0)
    medium: int = Field(default=0, ge=0)
    low: int = Field(default=0, ge=0)


class DashboardTrendSeries(BaseModel):
    repository_name: str
    timestamps: list[datetime] = Field(default_factory=list)
    health_scores: list[float] = Field(default_factory=list)

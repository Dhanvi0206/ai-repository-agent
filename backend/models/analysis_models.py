from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RepositoryHealthPoint(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    health_score: float = Field(..., ge=0.0, le=100.0)
    security_score: float = Field(..., ge=0.0, le=100.0)
    code_quality_score: float = Field(..., ge=0.0, le=100.0)
    documentation_score: float = Field(..., ge=0.0, le=100.0)
    dependency_score: float = Field(..., ge=0.0, le=100.0)


class HistoricalAnalysisSeries(BaseModel):
    repository_id: str
    points: list[RepositoryHealthPoint] = Field(default_factory=list)


class RepositoryTrendSnapshot(BaseModel):
    repository_id: str
    previous_score: float | None = Field(default=None, ge=0.0, le=100.0)
    current_score: float = Field(..., ge=0.0, le=100.0)
    trend: str

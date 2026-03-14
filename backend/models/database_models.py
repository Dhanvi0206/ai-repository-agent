from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.models.reasoning_models import SeverityLevel


def _generated_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class Repository(BaseModel):
    repository_id: str = Field(default_factory=lambda: _generated_id("repo"))
    repository_name: str
    owner: str
    language: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_analysis_time: datetime | None = None


class AnalysisResult(BaseModel):
    analysis_id: str = Field(default_factory=lambda: _generated_id("analysis"))
    repository_id: str
    health_score: float = Field(..., ge=0.0, le=100.0)
    security_score: float = Field(..., ge=0.0, le=100.0)
    quality_score: float = Field(..., ge=0.0, le=100.0)
    documentation_score: float = Field(..., ge=0.0, le=100.0)
    dependency_score: float = Field(..., ge=0.0, le=100.0)
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)


class SecurityIssue(BaseModel):
    issue_id: str = Field(default_factory=lambda: _generated_id("sec"))
    repository_id: str
    file_path: str
    line_number: int | None = None
    severity: SeverityLevel
    issue_type: str
    reasoning: str
    fix_suggestion: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class DependencyIssue(BaseModel):
    issue_id: str = Field(default_factory=lambda: _generated_id("dep"))
    repository_id: str
    dependency_name: str
    version: str | None = None
    vulnerability_id: str | None = None
    severity: SeverityLevel
    recommended_fix: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class CodeQualityIssue(BaseModel):
    issue_id: str = Field(default_factory=lambda: _generated_id("quality"))
    repository_id: str
    file_path: str
    issue_type: str
    complexity_score: float | None = Field(default=None, ge=0.0)
    recommendation: str
    severity: SeverityLevel = "medium"
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentationIssue(BaseModel):
    issue_id: str = Field(default_factory=lambda: _generated_id("docs"))
    repository_id: str
    file_path: str
    missing_docstring: bool = False
    missing_readme_sections: list[str] = Field(default_factory=list)
    recommendation: str | None = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class DeveloperScore(BaseModel):
    developer_id: str = Field(default_factory=lambda: _generated_id("dev"))
    repository_id: str
    developer_name: str
    pr_acceptance_rate: float = Field(..., ge=0.0, le=1.0)
    bug_frequency: float = Field(..., ge=0.0, le=1.0)
    code_quality_score: float = Field(..., ge=0.0, le=100.0)
    documentation_score: float = Field(..., ge=0.0, le=100.0)
    reputation_score: float = Field(..., ge=0.0, le=1.0)
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentExecutionLog(BaseModel):
    execution_id: str = Field(default_factory=lambda: _generated_id("exec"))
    agent_name: str
    repository_id: str
    execution_time: float = Field(..., ge=0.0)
    status: str
    issues_found: int = Field(default=0, ge=0)
    accuracy_score: float | None = Field(default=None, ge=0.0, le=1.0)
    executed_at: datetime = Field(default_factory=datetime.utcnow)

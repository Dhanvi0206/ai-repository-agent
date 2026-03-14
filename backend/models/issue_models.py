from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from backend.models.reasoning_models import SeverityLevel


class BaseIssueRecord(BaseModel):
    repository_id: str
    file_path: str
    issue_type: str
    severity: SeverityLevel
    reasoning: str
    recommendation: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class SecurityIssueRecord(BaseIssueRecord):
    line_number: int | None = None
    vulnerability_category: str | None = None


class DependencyIssueRecord(BaseModel):
    repository_id: str
    dependency_name: str
    version: str | None = None
    vulnerability_id: str | None = None
    severity: SeverityLevel
    reasoning: str
    recommendation: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class CodeQualityIssueRecord(BaseIssueRecord):
    complexity_score: float | None = Field(default=None, ge=0.0)


class DocumentationIssueRecord(BaseModel):
    repository_id: str
    file_path: str
    missing_docstring: bool = False
    missing_readme_sections: list[str] = Field(default_factory=list)
    recommendation: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)

from typing import Literal

from pydantic import BaseModel, Field


SeverityLevel = Literal["low", "medium", "high", "critical"]


class AgentReasoningOutput(BaseModel):
    agent: str
    issue_type: str
    file_path: str
    line_number: int | None = None
    analysis: str
    reasoning: str
    severity: SeverityLevel
    recommendation: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class AgentCritique(BaseModel):
    critic_agent: str
    target_agent: str
    issue_key: str
    result: Literal["confirmed", "questioned", "not_applicable"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    notes: str


class DebateResult(BaseModel):
    issue_key: str
    status: Literal["accepted", "warning", "rejected"]
    outcome: str
    supporting_agents: list[str] = Field(default_factory=list)
    opposing_agents: list[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)


class ConsensusIssue(BaseModel):
    issue: str
    issue_key: str
    file_path: str
    line_number: int | None = None
    severity: SeverityLevel
    confidence: float = Field(..., ge=0.0, le=1.0)
    recommendation: str
    detected_by: list[str] = Field(default_factory=list)
    verified_by: list[str] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high", "critical"] = "medium"
    status: Literal["accepted", "warning", "discarded"]
    reasoning_chain: list[str] = Field(default_factory=list)

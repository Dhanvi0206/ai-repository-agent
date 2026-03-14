from pydantic import AliasChoices, BaseModel, ConfigDict, Field, HttpUrl

from backend.models.reasoning_models import (
    AgentCritique,
    AgentReasoningOutput,
    ConsensusIssue,
    DebateResult,
    SeverityLevel,
)


class HealthResponse(BaseModel):
    status: str
    service: str
    message: str


class AnalyzeRepositoryRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    repo_url: HttpUrl = Field(
        ...,
        alias="repository_url",
        validation_alias=AliasChoices("repository_url", "repo_url"),
        description="GitHub repository URL to analyze",
    )


class CompareRepositoriesRequest(BaseModel):
    repo_a_id: str = Field(..., min_length=1, description="First analyzed repository identifier")
    repo_b_id: str = Field(..., min_length=1, description="Second analyzed repository identifier")


class RepositoryMetadata(BaseModel):
    repo_url: HttpUrl
    source: str
    clone_status: str
    owner: str | None = None
    repository_name: str | None = None
    branch: str | None = None
    local_path: str | None = None
    cache_hit: bool = False


class AgentIssue(BaseModel):
    file_path: str = Field(..., description="Repository-relative file path")
    line_number: int | None = Field(
        default=None,
        ge=1,
        description="Line number associated with the issue when available",
    )
    issue_type: str = Field(..., description="Short issue category reported by the agent")
    severity: SeverityLevel = Field(..., description="Risk or impact severity")
    description: str = Field(..., description="Human-readable explanation of the issue")
    reasoning: str = Field(
        default="",
        description="Explanation of why the issue was detected",
    )
    recommendation: str = Field(..., description="Suggested fix or next step")
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Agent confidence score between 0 and 1",
    )


class AgentResponse(BaseModel):
    agent_name: str = Field(..., description="Unique identifier for the agent")
    issues: list[AgentIssue] = Field(
        default_factory=list,
        description="Issues found by the agent in standardized format",
    )


class AggregatedAnalysis(BaseModel):
    target_repository: HttpUrl
    current_phase: str
    agents_planned: list[str]
    executed_agents: list[str]
    agents_executed: int = 0
    total_issues: int
    agent_results: list[AgentResponse]
    reasoning_outputs: list[AgentReasoningOutput] = Field(default_factory=list)
    critiques: list[AgentCritique] = Field(default_factory=list)
    debates: list[DebateResult] = Field(default_factory=list)
    consensus_issues: list[ConsensusIssue] = Field(default_factory=list)
    knowledge_insights: dict = Field(default_factory=dict)
    execution_log: list[dict] = Field(default_factory=list)
    analysis_time: float = 0.0
    summary: str


class HealthScore(BaseModel):
    score: float | None = Field(default=None, ge=0.0, le=100.0)
    status: str
    message: str
    security_score: float | None = Field(default=None, ge=0.0, le=100.0)
    code_quality_score: float | None = Field(default=None, ge=0.0, le=100.0)
    documentation_score: float | None = Field(default=None, ge=0.0, le=100.0)
    dependency_score: float | None = Field(default=None, ge=0.0, le=100.0)
    maintainability_score: float | None = Field(default=None, ge=0.0, le=100.0)
    developer_reputation_score: float | None = Field(default=None, ge=0.0, le=1.0)
    health_trend: str | None = None
    intelligence_summary: dict = Field(default_factory=dict)


class AnalyzeRepositoryResponse(BaseModel):
    status: str
    repo_url: HttpUrl
    message: str
    repository: RepositoryMetadata
    analysis: AggregatedAnalysis
    health_score: HealthScore

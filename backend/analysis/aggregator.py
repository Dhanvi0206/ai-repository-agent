from backend.models.reasoning_models import (
    AgentCritique,
    AgentReasoningOutput,
    ConsensusIssue,
    DebateResult,
)
from backend.models.response_models import (
    AggregatedAnalysis,
    AgentResponse,
)


class AnalysisAggregator:
    """Aggregates outputs from multiple agents into a single response model."""

    def build_placeholder_summary(
        self,
        repo_url: str,
        agent_results: list[AgentResponse] | None = None,
        reasoning_outputs: list[AgentReasoningOutput] | None = None,
        critiques: list[AgentCritique] | None = None,
        debates: list[DebateResult] | None = None,
        consensus_issues: list[ConsensusIssue] | None = None,
        knowledge_insights: dict | None = None,
        execution_log: list[dict] | None = None,
        analysis_time: float = 0.0,
    ) -> AggregatedAnalysis:
        agent_results = agent_results or []
        reasoning_outputs = reasoning_outputs or []
        critiques = critiques or []
        debates = debates or []
        consensus_issues = consensus_issues or []
        knowledge_insights = knowledge_insights or {}
        execution_log = execution_log or []
        executed_agents = [result.agent_name for result in agent_results]

        return AggregatedAnalysis(
            target_repository=repo_url,
            current_phase="phase-4-orchestrator-engine",
            agents_planned=[
                "Code Review Agent",
                "Security Agent",
                "Dependency Vulnerability Agent",
                "Documentation Agent",
                "Code Quality Agent",
                "Learning Agent",
                "Contribution Intelligence Agent",
                "Reporting Agent",
            ],
            executed_agents=executed_agents,
            agents_executed=len(executed_agents),
            total_issues=sum(len(result.issues) for result in agent_results),
            agent_results=agent_results,
            reasoning_outputs=reasoning_outputs,
            critiques=critiques,
            debates=debates,
            consensus_issues=consensus_issues,
            knowledge_insights=knowledge_insights,
            execution_log=execution_log,
            analysis_time=analysis_time,
            summary=(
                "Central orchestrator executed the agent pipeline with scheduling, "
                "fault tolerance, peer reasoning, collaboration fusion, knowledge learning, and final aggregation."
            ),
        )

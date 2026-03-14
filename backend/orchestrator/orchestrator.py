from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError, as_completed
from time import perf_counter

from backend.agents.agent_critic import AgentCritic, critique_agent_results
from backend.agents.agent_debate import AgentDebate, resolve_agent_conflicts
from backend.agents.agent_manager import AgentManager
from backend.agents.reasoning_engine import build_reasoning_outputs
from backend.analysis.aggregator import AnalysisAggregator
from backend.collaboration.collaboration_engine import CollaborationEngine
from backend.knowledge.fix_suggestion_engine import FixSuggestionEngine
from backend.knowledge.knowledge_metrics import calculate_knowledge_metrics
from backend.knowledge.knowledge_store import KnowledgeStore
from backend.knowledge.pattern_detector import PatternDetector
from backend.knowledge.similarity_engine import SimilarityEngine
from backend.models.response_models import AgentResponse, AnalyzeRepositoryResponse
from backend.orchestrator.execution_log import ExecutionLogManager
from backend.orchestrator.pipeline_manager import PipelineManager
from backend.repository.repo_fetcher import RepositoryFetcher
from backend.scoring.health_score import HealthScoreCalculator
from backend.stability.logging_system import log_event
from backend.stability.performance_optimizer import PerformanceOptimizer
from backend.stability.retry_manager import retry_operation


class RepositoryOrchestrator:
    """Coordinates repository fetch, analysis, and scoring steps."""

    AGENT_TIMEOUT_SECONDS = 30

    def __init__(self) -> None:
        self.repo_fetcher = RepositoryFetcher()
        self.aggregator = AnalysisAggregator()
        self.health_score_calculator = HealthScoreCalculator()
        self.agent_critic = AgentCritic()
        self.agent_debate = AgentDebate()
        self.collaboration_engine = CollaborationEngine()
        self.knowledge_store = KnowledgeStore()
        self.pattern_detector = PatternDetector(self.knowledge_store)
        self.fix_suggestion_engine = FixSuggestionEngine()
        self.similarity_engine = SimilarityEngine(self.knowledge_store)
        self.pipeline_manager = PipelineManager()
        self.performance_optimizer = PerformanceOptimizer()
        self.agent_manager = AgentManager()
        self.agents = self.agent_manager.load_agents()

    def run_agent_pipeline(
        self,
        repository_context: dict,
        code_chunks: list[dict],
        progress_callback=None,
    ) -> dict:
        """Execute the full agent pipeline with scheduling, logging, and resilience."""
        pipeline_started_at = perf_counter()
        execution_log_manager = ExecutionLogManager()
        scheduled_agents = self.pipeline_manager.sort_agents(self.agents)
        prioritized_chunks = self.pipeline_manager.build_incremental_batch(code_chunks)
        prioritized_chunks = self.performance_optimizer.optimize_chunks(prioritized_chunks)

        if not scheduled_agents:
            return {
                "repository": repository_context.get("repository"),
                "agents_executed": 0,
                "results": [],
                "execution_log": [],
                "analysis_time": 0.0,
            }

        results: list[AgentResponse] = []
        execution_log: list[dict] = []
        worker_count = self.performance_optimizer.get_optimal_worker_count(len(scheduled_agents))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_to_agent = {
                executor.submit(
                    self._execute_agent,
                    agent,
                    prioritized_chunks,
                    repository_context,
                    execution_log_manager,
                    progress_callback,
                ): agent
                for agent in scheduled_agents
            }

            for future in as_completed(future_to_agent):
                result, log_entry = future.result()
                execution_log.append(log_entry)
                if result is not None:
                    results.append(result)

        return {
            "repository": repository_context.get("repository"),
            "agents_executed": len(results),
            "results": results,
            "execution_log": sorted(execution_log, key=lambda item: item["start_offset"]),
            "analysis_time": round(perf_counter() - pipeline_started_at, 4),
        }

    def _execute_agent(
        self,
        agent,
        code_chunks: list[dict],
        repository_context: dict,
        execution_log_manager: ExecutionLogManager,
        progress_callback=None,
    ) -> tuple[AgentResponse | None, dict]:
        started_at = perf_counter()
        lead_file = code_chunks[0].get("file", "repository") if code_chunks else "repository"
        if progress_callback:
            progress_callback(
                {
                    "agent": agent.agent_name,
                    "status": "running",
                    "message": f"Analyzing {lead_file}",
                    "files_analyzed": len({chunk.get('file') for chunk in code_chunks if chunk.get('file')}),
                }
            )
        try:
            log_event(agent.agent_name, "START", "Agent execution started")
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    retry_operation,
                    agent.analyze,
                    code_chunks,
                    repository_context,
                    retries=2,
                )
                result = future.result(timeout=self.AGENT_TIMEOUT_SECONDS)
            finished_at = perf_counter()
            log_entry = execution_log_manager.build_record(
                agent.agent_name,
                started_at,
                finished_at,
                "completed",
            ).to_dict()
            log_event(
                agent.agent_name,
                "COMPLETE",
                "Agent execution completed",
                execution_time=log_entry["execution_time"],
                issues_found=len(result.issues),
            )
            if progress_callback:
                progress_callback(
                    {
                        "agent": agent.agent_name,
                        "status": "completed",
                        "message": f"Analyzed {len({chunk.get('file') for chunk in code_chunks if chunk.get('file')})} files",
                        "execution_time": log_entry["execution_time"],
                        "files_analyzed": len({chunk.get('file') for chunk in code_chunks if chunk.get('file')}),
                    }
                )
            return result, log_entry
        except FuturesTimeoutError as exc:
            finished_at = perf_counter()
            log_entry = execution_log_manager.build_record(
                agent.agent_name,
                started_at,
                finished_at,
                "failed",
                error=f"Agent timed out after {self.AGENT_TIMEOUT_SECONDS} seconds",
            ).to_dict()
            log_event(agent.agent_name, "TIMEOUT", "Agent execution timed out")
            if progress_callback:
                progress_callback(
                    {
                        "agent": agent.agent_name,
                        "status": "failed",
                        "message": f"Timed out after {self.AGENT_TIMEOUT_SECONDS} seconds",
                        "execution_time": log_entry["execution_time"],
                    }
                )
            return None, log_entry
        except Exception as exc:
            finished_at = perf_counter()
            log_entry = execution_log_manager.build_record(
                agent.agent_name,
                started_at,
                finished_at,
                "failed",
                error=str(exc),
            ).to_dict()
            log_event(agent.agent_name, "ERROR", "Agent execution failed", error=str(exc))
            if progress_callback:
                progress_callback(
                    {
                        "agent": agent.agent_name,
                        "status": "failed",
                        "message": str(exc),
                        "execution_time": log_entry["execution_time"],
                    }
                )
            return None, log_entry

    def analyze_repository(self, repo_url: str, progress_callback=None) -> AnalyzeRepositoryResponse:
        repository_metadata = self.repo_fetcher.prepare_repository_metadata(repo_url)
        ingestion_result = self.repo_fetcher.prepare_repository_for_analysis(repo_url)
        ingestion_result["knowledge_context"] = self.similarity_engine.detect_similar_repository(
            ingestion_result
        )
        orchestrator_output = self.run_agent_pipeline(
            ingestion_result,
            ingestion_result["ranked_contexts"],
            progress_callback,
        )
        agent_results = orchestrator_output["results"]
        reasoning_outputs = build_reasoning_outputs(agent_results)
        critiques = critique_agent_results(reasoning_outputs)
        debates = resolve_agent_conflicts(reasoning_outputs, critiques)
        consensus_issues = self.collaboration_engine.collaborate(
            reasoning_outputs,
            debates,
        )
        detected_patterns = self.pattern_detector.detect_patterns(consensus_issues)
        fix_suggestions = self.fix_suggestion_engine.suggest_fixes(
            consensus_issues,
            detected_patterns,
        )
        self.knowledge_store.store_analysis(ingestion_result, consensus_issues)
        knowledge_metrics = calculate_knowledge_metrics(self.knowledge_store.get_patterns())
        knowledge_insights = {
            "similar_repository": ingestion_result["knowledge_context"],
            "detected_patterns": detected_patterns,
            "fix_suggestions": fix_suggestions,
            "knowledge_metrics": knowledge_metrics,
        }
        analysis_summary = self.aggregator.build_placeholder_summary(
            repo_url,
            agent_results,
            reasoning_outputs,
            critiques,
            debates,
            consensus_issues,
            knowledge_insights,
            orchestrator_output["execution_log"],
            orchestrator_output["analysis_time"],
        )
        health_score = self.health_score_calculator.calculate_score(
            ingestion_result,
            consensus_issues,
        )

        return AnalyzeRepositoryResponse(
            status="accepted",
            repo_url=repo_url,
            message=(
                "Repository analysis request received. The orchestrator executed "
                "the multi-agent pipeline, tracked execution, and aggregated results."
            ),
            repository=repository_metadata,
            analysis=analysis_summary,
            health_score=health_score,
        )

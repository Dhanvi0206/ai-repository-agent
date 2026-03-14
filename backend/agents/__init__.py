"""Agent package for repository analysis agents."""

from backend.agents.agent_critic import AgentCritic, critique_agent_results
from backend.agents.agent_debate import AgentDebate, resolve_agent_conflicts
from backend.agents.agent_manager import AgentManager
from backend.agents.agent_registry import get_registered_agents
from backend.agents.base_agent import BaseAgent
from backend.agents.code_quality_agent import CodeQualityAgent
from backend.agents.code_review_agent import CodeReviewAgent
from backend.agents.contribution_agent import ContributionAgent
from backend.agents.consensus_engine import ConsensusEngine
from backend.agents.dependency_agent import DependencyAgent
from backend.agents.documentation_agent import DocumentationAgent
from backend.agents.learning_agent import LearningAgent
from backend.agents.reasoning_engine import build_reasoning_outputs
from backend.agents.security_agent import SecurityAgent

__all__ = [
    "AgentCritic",
    "AgentDebate",
    "AgentManager",
    "BaseAgent",
    "CodeQualityAgent",
    "CodeReviewAgent",
    "ConsensusEngine",
    "ContributionAgent",
    "DependencyAgent",
    "DocumentationAgent",
    "LearningAgent",
    "SecurityAgent",
    "build_reasoning_outputs",
    "critique_agent_results",
    "get_registered_agents",
    "resolve_agent_conflicts",
]

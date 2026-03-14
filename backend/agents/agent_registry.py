from __future__ import annotations

from backend.agents.code_quality_agent import CodeQualityAgent
from backend.agents.code_review_agent import CodeReviewAgent
from backend.agents.contribution_agent import ContributionAgent
from backend.agents.dependency_agent import DependencyAgent
from backend.agents.documentation_agent import DocumentationAgent
from backend.agents.learning_agent import LearningAgent
from backend.agents.security_agent import SecurityAgent


def get_registered_agents() -> list:
    """Return the default multi-agent set used by the orchestrator."""
    return [
        SecurityAgent(),
        DependencyAgent(),
        CodeReviewAgent(),
        CodeQualityAgent(),
        DocumentationAgent(),
        ContributionAgent(),
        LearningAgent(),
    ]

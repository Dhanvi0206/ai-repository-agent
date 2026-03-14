from __future__ import annotations

from backend.agents.agent_registry import get_registered_agents


class AgentManager:
    """Provides a simple integration point for orchestrator-side agent loading."""

    def load_agents(self) -> list:
        return get_registered_agents()

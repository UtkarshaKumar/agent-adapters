from src.adapters.base import AgentType

from .claude import ClaudeAgent
from .gemini import GeminiAgent
from .minimax import MinimaxAgent
from .kimi import KimiAgent

__all__ = ["ClaudeAgent", "GeminiAgent", "MinimaxAgent", "KimiAgent", "AgentType"]


def get_agent(agent_type: AgentType, api_key: str, **kwargs):
    """Factory function to get an agent adapter by type."""
    agents = {
        AgentType.CLAUDE: ClaudeAgent,
        AgentType.GEMINI: GeminiAgent,
        AgentType.MINIMAX: MinimaxAgent,
        AgentType.KIMI: KimiAgent,
    }

    if agent_type not in agents:
        raise ValueError(f"Unknown agent type: {agent_type}")

    return agents[agent_type](api_key=api_key, **kwargs)

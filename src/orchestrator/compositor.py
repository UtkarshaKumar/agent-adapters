from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import json

from src.adapters.base import BaseAgent, Task, AgentResponse, AgentType


class OrchestratorStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class OrchestratorConfig:
    composio_url: str = "http://localhost:3000"
    agentops_enabled: bool = True
    worktree_base: str = "/tmp/agent-worktrees"
    github_repo: str = ""


@dataclass
class OrchestratorResult:
    status: OrchestratorStatus
    responses: List[AgentResponse]
    total_cost: float
    total_latency_ms: int
    errors: List[str]


class ComposioOrchestrator:
    """Main orchestrator for multi-agent coordination via Composio."""

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.agents: Dict[AgentType, BaseAgent] = {}
        self.status = OrchestratorStatus.IDLE

    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator."""
        self.agents[agent.get_type()] = agent

    def run_task(self, task: Task) -> AgentResponse:
        """Run a single task with the appropriate agent."""
        agent = self.agents.get(task.agent_type)
        if not agent:
            raise ValueError(f"No agent registered for type: {task.agent_type}")
        return agent.run(task)

    def run_parallel(self, tasks: List[Task]) -> List[AgentResponse]:
        """Run multiple tasks in parallel with different agents."""
        import concurrent.futures

        responses = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            futures = {executor.submit(self.run_task, task): task for task in tasks}
            for future in concurrent.futures.as_completed(futures):
                responses.append(future.result())

        return responses

    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status."""
        return {
            "status": self.status.value,
            "registered_agents": [a.value for a in self.agents.keys()],
            "config": {
                "composio_url": self.config.composio_url,
                "agentops_enabled": self.config.agentops_enabled,
            },
        }

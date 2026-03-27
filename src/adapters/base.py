from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentType(Enum):
    CLAUDE = "claude"
    GEMINI = "gemini"
    MINIMAX = "minimax"
    KIMI = "kimi"


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    id: str
    prompt: str
    agent_type: AgentType
    context: Dict[str, Any]
    tools: List[str]
    metadata: Dict[str, Any]


@dataclass
class AgentResponse:
    success: bool
    output: str
    error: Optional[str]
    metrics: Dict[str, Any]
    task_id: str


@dataclass
class Capability:
    name: str
    description: str
    latency_ms: int
    supports_streaming: bool = False


class BaseAgent(ABC):
    def __init__(self, api_key: str, agent_type: AgentType):
        self.api_key = api_key
        self.agent_type = agent_type
        self.session_id = None

    @abstractmethod
    def run(self, task: Task) -> AgentResponse:
        pass

    @abstractmethod
    def get_capabilities(self) -> List[Capability]:
        pass

    def get_type(self) -> AgentType:
        return self.agent_type

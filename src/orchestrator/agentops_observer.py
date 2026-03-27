import agentops
from typing import Optional
from dataclasses import dataclass


@dataclass
class AgentOpsConfig:
    api_key: Optional[str] = None
    tags: list = None
    auto_start_session: bool = True


class AgentOpsObserver:
    """AgentOps SDK integration for observability."""
    
    _instance = None
    _session = None
    
    def __init__(self, config: AgentOpsConfig = None):
        self.config = config or AgentOpsConfig()
        self._initialized = False
    
    def initialize(self):
        if self._initialized:
            return
        
        try:
            agentops.init(
                api_key=self.config.api_key,
                tags=self.config.tags or [],
                auto_start_session=self.config.auto_start_session
            )
            self._initialized = True
        except Exception:
            self._initialized = False
    
    def start_session(self, tags: list = None):
        try:
            if hasattr(agentops, 'start_session'):
                agentops.start_session(tags=tags)
            elif hasattr(agentops, 'Session'):
                self._session = agentops.Session()
                self._session.start()
        except Exception:
            pass
    
    def end_session(self, success: bool = True):
        try:
            if self._session:
                self._session.end(success=success)
            elif hasattr(agentops, 'end_session'):
                agentops.end_session(success=success)
        except Exception:
            pass
    
    def record_action(self, agent_type: str, action: str, success: bool, 
                      latency_ms: int, cost: float = 0.0, metadata: dict = None):
        try:
            event = {
                "agent": agent_type,
                "action": action,
                "success": success,
                "latency_ms": latency_ms,
                "cost": cost,
                "metadata": metadata or {}
            }
            
            if hasattr(agentops, 'track'):
                agentops.track(event)
            elif hasattr(agentops, 'log'):
                agentops.log(event)
        except Exception:
            pass
    
    def get_session_url(self) -> str:
        try:
            if hasattr(agentops, 'get_session_url'):
                return agentops.get_session_url()
        except Exception:
            pass
        return ""


def get_observer(config: AgentOpsConfig = None) -> AgentOpsObserver:
    """Get singleton AgentOps observer instance."""
    if AgentOpsObserver._instance is None:
        AgentOpsObserver._instance = AgentOpsObserver(config)
    return AgentOpsObserver._instance

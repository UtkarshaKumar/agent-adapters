from typing import List
from .base import BaseAgent, Task, AgentResponse, Capability, AgentType
from ..orchestrator.agentops_observer import get_observer, AgentOpsConfig


class GeminiAgent(BaseAgent):
    """Gemini API wrapper adapter."""

    def __init__(self, api_key: str, agentops_key: str = None):
        super().__init__(api_key, AgentType.GEMINI)
        try:
            from google import genai

            self.client = genai.Client(api_key=api_key)
        except ImportError:
            raise RuntimeError(
                "google-genai not installed. Run: pip install google-genai"
            )
        
        observer_config = AgentOpsConfig(api_key=agentops_key, tags=["gemini", "agent-adapter"])
        self.ops_observer = get_observer(observer_config)
        self.ops_observer.initialize()

    def run(self, task: Task) -> AgentResponse:
        import time
        from google import genai

        start = time.time()
        self.ops_observer.start_session(tags=["gemini", task.id])

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=task.prompt,
            )

            elapsed_ms = int((time.time() - start) * 1000)
            
            cost = self._estimate_cost(prompt_tokens=len(task.prompt.split()), 
                                       completion_tokens=len(str(response.text).split()))

            self.ops_observer.record_action(
                agent_type="gemini",
                action="generate_content",
                success=True,
                latency_ms=elapsed_ms,
                cost=cost,
                metadata={
                    "model": "gemini-2.0-flash",
                    "task_id": task.id,
                    "output_length": len(str(response.text))
                }
            )
            self.ops_observer.end_session(success=True)

            return AgentResponse(
                success=True,
                output=str(response.text),
                error=None,
                metrics={
                    "latency_ms": elapsed_ms,
                    "agent": "gemini",
                    "model": "gemini-2.0-flash",
                    "cost": cost,
                },
                task_id=task.id,
            )
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            self.ops_observer.record_action(
                agent_type="gemini",
                action="error",
                success=False,
                latency_ms=elapsed_ms,
                metadata={"error": str(e)}
            )
            self.ops_observer.end_session(success=False)
            return AgentResponse(
                success=False,
                output="",
                error=str(e),
                metrics={"latency_ms": elapsed_ms, "agent": "gemini"},
                task_id=task.id,
            )

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        INPUT_COST_PER_1M = 0.075
        OUTPUT_COST_PER_1M = 0.30
        return (prompt_tokens / 1_000_000) * INPUT_COST_PER_1M + \
               (completion_tokens / 1_000_000) * OUTPUT_COST_PER_1M

    def get_capabilities(self) -> List[Capability]:
        return [
            Capability(
                "text-generation",
                "Generate text content",
                latency_ms=1000,
                supports_streaming=True,
            ),
            Capability("code-generation", "Write code snippets", latency_ms=2000),
            Capability("reasoning", "Chain-of-thought reasoning", latency_ms=3000),
        ]

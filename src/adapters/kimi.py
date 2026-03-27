from typing import List
from .base import BaseAgent, Task, AgentResponse, Capability, AgentType
from ..orchestrator.agentops_observer import get_observer, AgentOpsConfig


class KimiAgent(BaseAgent):
    """Kimi API wrapper adapter."""

    def __init__(self, api_key: str, base_url: str = "https://api.moonshot.cn/v1",
                 agentops_key: str = None):
        super().__init__(api_key, AgentType.KIMI)
        self.base_url = base_url
        self._client = None
        
        observer_config = AgentOpsConfig(api_key=agentops_key, tags=["kimi", "agent-adapter"])
        self.ops_observer = get_observer(observer_config)
        self.ops_observer.initialize()

    def _get_client(self):
        if self._client is None:
            try:
                import openai

                self._client = openai.OpenAI(api_key=api_key, base_url=base_url)
            except ImportError:
                raise RuntimeError("openai not installed. Run: pip install openai")
        return self._client

    def run(self, task: Task) -> AgentResponse:
        import time

        start = time.time()
        self.ops_observer.start_session(tags=["kimi", task.id])

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model="moonshot-v1-8k",
                messages=[{"role": "user", "content": task.prompt}],
                timeout=task.context.get("timeout", 300),
            )

            elapsed_ms = int((time.time() - start) * 1000)
            output = response.choices[0].message.content or ""
            
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            cost = self._estimate_cost(prompt_tokens, completion_tokens)

            self.ops_observer.record_action(
                agent_type="kimi",
                action="chat_completion",
                success=True,
                latency_ms=elapsed_ms,
                cost=cost,
                metadata={
                    "model": "moonshot-v1-8k",
                    "task_id": task.id,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens
                }
            )
            self.ops_observer.end_session(success=True)

            return AgentResponse(
                success=True,
                output=output,
                error=None,
                metrics={
                    "latency_ms": elapsed_ms,
                    "agent": "kimi",
                    "model": "moonshot-v1-8k",
                    "cost": cost,
                },
                task_id=task.id,
            )
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            self.ops_observer.record_action(
                agent_type="kimi",
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
                metrics={"latency_ms": elapsed_ms, "agent": "kimi"},
                task_id=task.id,
            )

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        INPUT_COST_PER_1K = 0.003
        OUTPUT_COST_PER_1K = 0.015
        return (prompt_tokens / 1000) * INPUT_COST_PER_1K + \
               (completion_tokens / 1000) * OUTPUT_COST_PER_1K

    def get_capabilities(self) -> List[Capability]:
        return [
            Capability(
                "text-generation",
                "Generate text content",
                latency_ms=900,
                supports_streaming=True,
            ),
            Capability("code-generation", "Write code snippets", latency_ms=1800),
            Capability("long-context", "Handle long documents", latency_ms=2000),
        ]

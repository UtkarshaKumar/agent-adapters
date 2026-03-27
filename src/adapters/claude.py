import subprocess
import json
import os
from pathlib import Path
from typing import List, Optional
from .base import BaseAgent, Task, AgentResponse, Capability, AgentType
from ..orchestrator.agentops_observer import get_observer, AgentOpsConfig


class ClaudeAgent(BaseAgent):
    """Claude Code CLI adapter - first-class native support."""

    def __init__(self, api_key: str, repo_path: str, agentops_key: str = None):
        super().__init__(api_key, AgentType.CLAUDE)
        self.repo_path = Path(repo_path)
        self.claude_path = self._find_claude_cli()
        
        observer_config = AgentOpsConfig(api_key=agentops_key, tags=["claude", "agent-adapter"])
        self.ops_observer = get_observer(observer_config)
        self.ops_observer.initialize()

    def _find_claude_cli(self) -> str:
        path = subprocess.run(
            ["which", "claude"], capture_output=True, text=True
        ).stdout.strip()
        if not path:
            raise RuntimeError(
                "Claude Code CLI not found. Install from https://claude.ai/code"
            )
        return path

    def run(self, task: Task) -> AgentResponse:
        import time

        start = time.time()
        self.ops_observer.start_session(tags=["claude", task.id])

        try:
            result = subprocess.run(
                [self.claude_path, "code", "--print", task.prompt],
                capture_output=True,
                text=True,
                timeout=task.context.get("timeout", 300),
                cwd=self.repo_path,
            )

            elapsed_ms = int((time.time() - start) * 1000)
            success = result.returncode == 0

            self.ops_observer.record_action(
                agent_type="claude",
                action="claude_code_execution",
                success=success,
                latency_ms=elapsed_ms,
                cost=0.0,
                metadata={
                    "exit_code": result.returncode,
                    "task_id": task.id,
                    "prompt_length": len(task.prompt)
                }
            )

            return AgentResponse(
                success=success,
                output=result.stdout,
                error=result.stderr if not success else None,
                metrics={
                    "latency_ms": elapsed_ms,
                    "agent": "claude",
                    "exit_code": result.returncode,
                },
                task_id=task.id,
            )
        except subprocess.TimeoutExpired:
            self.ops_observer.record_action(
                agent_type="claude",
                action="timeout",
                success=False,
                latency_ms=int((time.time() - start) * 1000),
                metadata={"task_id": task.id}
            )
            self.ops_observer.end_session(success=False)
            return AgentResponse(
                success=False,
                output="",
                error="Task timed out",
                metrics={
                    "latency_ms": int((time.time() - start) * 1000),
                    "agent": "claude",
                },
                task_id=task.id,
            )
        except Exception as e:
            self.ops_observer.record_action(
                agent_type="claude",
                action="error",
                success=False,
                latency_ms=int((time.time() - start) * 1000),
                metadata={"error": str(e)}
            )
            self.ops_observer.end_session(success=False)
            return AgentResponse(
                success=False,
                output="",
                error=str(e),
                metrics={
                    "latency_ms": int((time.time() - start) * 1000),
                    "agent": "claude",
                },
                task_id=task.id,
            )
        finally:
            self.ops_observer.end_session(success=True)

    def get_capabilities(self) -> List[Capability]:
        return [
            Capability(
                "code-generation",
                "Write and edit code",
                latency_ms=2000,
                supports_streaming=True,
            ),
            Capability(
                "code-review",
                "Review code changes",
                latency_ms=3000,
                supports_streaming=True,
            ),
            Capability("debugging", "Find and fix bugs", latency_ms=5000),
            Capability("refactoring", "Restructure code", latency_ms=4000),
        ]

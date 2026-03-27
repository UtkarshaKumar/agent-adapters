# Agent Adapters — Multi-Agent Orchestration Platform

> Composio-powered multi-agent orchestration with Claude, Gemini, Minimax, and Kimi adapters.

## Architecture

```
Task Source:          GitHub Issues
       ↓
Orchestrator:         Composio Agent Orchestrator (open source, localhost:3000 dashboard)
       ↓
Agent Adapters:
  Claude   → Claude Code CLI (native, first-class support)
  Gemini   → Gemini API wrapper (thin adapter)
  Minimax  → Minimax API wrapper (thin adapter)
  Kimi     → Kimi API wrapper (thin adapter)
       ↓
Observability:        AgentOps (session replay, multi-agent viz, cost tracking)
       ↓
Output:               Each agent → own git worktree → own branch → PR → main
```

## Quick Start

```bash
pip install agent-adapters
python -m src.orchestrator --issue 123
```

## AgentOps Observability

Each adapter integrates with **AgentOps** for comprehensive observability:

- **Session replay** — record and replay agent execution sessions
- **Multi-agent visualization** — track all agents in the orchestrator
- **Cost tracking** — per-agent and aggregate cost metrics
- **Latency monitoring** — P50/P95/P99 action latency
- **Error tracking** — failed actions with full context

```python
from agent_adapters import get_agent, AgentType

agent = get_agent(
    AgentType.GEMINI, 
    api_key="your-key",
    agentops_key="your-agentops-key"  # Optional but recommended
)
```

View your session dashboard at [app.agentops.ai](https://app.agentops.ai)

## Agent Adapter Interface

All adapters implement:

```python
class BaseAgent(ABC):
    @abstractmethod
    def run(self, task: Task) -> AgentResponse:
        pass

    @abstractmethod
    def get_capabilities(self) -> List[Capability]:
        pass
```

## Project Structure

```
agent-adapters/
├── src/
│   ├── adapters/          # Agent adapter implementations
│   │   ├── base.py        # BaseAgent abstract class
│   │   ├── claude.py      # Claude Code CLI adapter
│   │   ├── gemini.py       # Gemini API adapter
│   │   ├── minimax.py      # Minimax API adapter
│   │   └── kimi.py         # Kimi API adapter
│   ├── orchestrator/      # Composio orchestration layer
│   │   ├── compositor.py  # Main orchestrator
│   │   └── agentops_observer.py  # AgentOps SDK integration
│   ├── git/               # Git worktree management
│   │   └── worktree.py    # Branch/PR workflow
│   ├── github/            # GitHub Issues integration
│   │   └── issues.py      # Issue fetcher
│   └── tools/             # Shared composio tools
├── tests/                 # Unit tests
└── examples/              # Usage examples
```

## License

MIT
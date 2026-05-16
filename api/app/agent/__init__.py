"""Tool-using chat agent.

Public surface: `run_agent` plus the `Tool` / `ToolContext` types you need
to add new tools. See `agent/README.md` and `agent/tools/__init__.py`.
"""

from app.agent.loop import AgentEvent, run_agent
from app.agent.tools import REGISTRY, Tool, ToolContext

__all__ = ["AgentEvent", "REGISTRY", "Tool", "ToolContext", "run_agent"]

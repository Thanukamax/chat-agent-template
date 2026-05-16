"""Tool registry for the chat agent.

A tool is an async function plus a JSON-schema description. Register one with
the `@tool` decorator. The registry exposes both the OpenAI/Groq tool-schema
list (for sending to the model) and a `dispatch` helper (for running a chosen
tool).

To add a new tool, create a module under `app.agent.tools.<your_module>`,
define async functions decorated with `@tool`, and import the module at the
bottom of this file so it's loaded into the registry.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolContext:
    """Per-request context handed to every tool invocation.

    Generic on purpose. Stash whatever your tools need (DB session, user ID,
    request scope) in `extras`. Each tool then reads `ctx.extras["session"]`
    or similar.
    """

    extras: dict[str, Any] = field(default_factory=dict)


ToolHandler = Callable[..., Awaitable[Any]]


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler

    def openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class Registry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def schemas(self) -> list[dict[str, Any]]:
        return [t.openai_schema() for t in self._tools.values()]

    def names(self) -> list[str]:
        return list(self._tools)

    async def dispatch(self, name: str, args: dict[str, Any], ctx: ToolContext) -> Any:
        tool = self._tools.get(name)
        if tool is None:
            return {"error": f"unknown tool: {name}"}
        sig = inspect.signature(tool.handler)
        kwargs = dict(args)
        if "ctx" in sig.parameters:
            kwargs["ctx"] = ctx
        try:
            return await tool.handler(**kwargs)
        except Exception as exc:  # noqa: BLE001 — tools must never crash the loop
            return {"error": f"{type(exc).__name__}: {exc}"}


REGISTRY = Registry()


def tool(name: str, description: str, parameters: dict[str, Any]) -> Callable[[ToolHandler], ToolHandler]:
    """Decorator: register an async function as an agent tool."""

    def wrap(handler: ToolHandler) -> ToolHandler:
        REGISTRY.register(Tool(name=name, description=description, parameters=parameters, handler=handler))
        return handler

    return wrap


# Side-effect imports — each module decorates its handlers, which adds them
# to REGISTRY. To enable a new tool module, add an import line here.
from app.agent.tools import fs as _fs  # noqa: E402, F401
from app.agent.tools import notion as _notion  # noqa: E402, F401

# `meetings` is NOT imported on purpose — it's a reference shape for wiring
# tools to a database. See app/agent/tools/meetings.py for the pattern.

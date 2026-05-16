"""Multi-turn tool-using agent loop.

Uses the Groq SDK (OpenAI-compatible) for tool calling. One streamed completion
per iteration: text chunks flow live, tool calls accumulate, the loop dispatches
them and feeds results back until the model returns no more tool calls.

Swap to Gemini function-calling later by branching on `settings.ai_provider`
inside `run_agent` — the event shape stays the same.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal

from groq import Groq

from app.agent.prompts import SYSTEM
from app.agent.tools import REGISTRY, ToolContext
from app.config import get_settings

MODEL = "llama-3.3-70b-versatile"
MAX_ITERATIONS = 6


EventType = Literal["text", "tool_call", "tool_result", "done", "error"]


@dataclass
class AgentEvent:
    type: EventType
    data: Any = None

    def to_json(self) -> str:
        return json.dumps({"type": self.type, "data": self.data}, default=str)


def _client() -> Groq:
    settings = get_settings()
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY required")
    return Groq(api_key=settings.groq_api_key)


def _stream_iteration(messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, str]]]:
    """One non-async streaming call. Returns (content, tool_calls).

    Runs in a worker thread via `asyncio.to_thread` so the FastAPI event loop
    stays free. Streaming text chunks would require a different bridge — for the
    template, we collect the iteration's text and yield it as a single event.
    """
    stream = _client().chat.completions.create(
        model=MODEL,
        messages=messages,  # type: ignore[arg-type]
        tools=REGISTRY.schemas(),  # type: ignore[arg-type]
        tool_choice="auto",
        stream=True,
    )

    content = ""
    tool_calls: list[dict[str, str]] = []

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            content += delta.content
        if delta.tool_calls:
            for tc_delta in delta.tool_calls:
                idx = tc_delta.index
                while len(tool_calls) <= idx:
                    tool_calls.append({"id": "", "name": "", "arguments": ""})
                if tc_delta.id:
                    tool_calls[idx]["id"] = tc_delta.id
                if tc_delta.function and tc_delta.function.name:
                    tool_calls[idx]["name"] = tc_delta.function.name
                if tc_delta.function and tc_delta.function.arguments:
                    tool_calls[idx]["arguments"] += tc_delta.function.arguments

    return content, tool_calls


async def run_agent(
    user_message: str,
    ctx: ToolContext,
    history: list[dict[str, Any]] | None = None,
) -> AsyncIterator[AgentEvent]:
    """Drive the agent loop and yield typed events.

    `history` is a list of OpenAI-style messages (role + content) from prior turns.
    The active project ID is taken from `ctx.project_id` and injected as a
    system addendum so the model always knows which project it's reasoning about.
    """

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM},
        {"role": "system", "content": f"Active project ID: {ctx.project_id}"},
    ]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    for iteration in range(MAX_ITERATIONS):
        try:
            content, tool_calls = await asyncio.to_thread(_stream_iteration, messages)
        except Exception as exc:  # noqa: BLE001
            yield AgentEvent(type="error", data={"message": str(exc), "iteration": iteration})
            return

        if content:
            yield AgentEvent(type="text", data=content)

        if not tool_calls:
            yield AgentEvent(type="done", data={"iterations": iteration + 1})
            return

        messages.append(
            {
                "role": "assistant",
                "content": content or None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"] or "{}"},
                    }
                    for tc in tool_calls
                ],
            }
        )

        for tc in tool_calls:
            try:
                args = json.loads(tc["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            yield AgentEvent(
                type="tool_call",
                data={"id": tc["id"], "name": tc["name"], "args": args},
            )
            result = await REGISTRY.dispatch(tc["name"], args, ctx)
            yield AgentEvent(
                type="tool_result",
                data={"id": tc["id"], "name": tc["name"], "result": result},
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result, default=str),
                }
            )

    yield AgentEvent(
        type="error",
        data={"message": f"max iterations ({MAX_ITERATIONS}) reached"},
    )

"""POST /agent — Server-Sent Events stream of typed agent events."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.agent import ToolContext, run_agent

router = APIRouter(tags=["agent"])


class AgentMessage(BaseModel):
    role: str
    content: str


class AgentBody(BaseModel):
    message: str
    history: list[AgentMessage] | None = None
    extras: dict[str, Any] | None = None


@router.post("/agent")
async def agent(body: AgentBody):
    print(f'\n[AGENT] "{body.message[:60]}"')

    ctx = ToolContext(extras=body.extras or {})
    history: list[dict[str, Any]] = (
        [{"role": m.role, "content": m.content} for m in body.history] if body.history else []
    )

    async def stream():
        async for event in run_agent(body.message, ctx, history=history):
            yield {"data": event.to_json()}
        yield {"data": "[DONE]"}

    return EventSourceResponse(stream())

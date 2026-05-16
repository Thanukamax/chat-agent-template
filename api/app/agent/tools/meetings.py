"""REFERENCE ONLY — shape for wiring agent tools to a database.

This file is NOT imported by `app/agent/tools/__init__.py` — its imports would
fail because this template has no DB layer. It is preserved as a worked
example of:

  - Reading per-request state out of `ctx.extras` (here: a SQLModel session
    and an active project ID).
  - Translating ORM rows into JSON-safe dicts inside the tool, so the model
    sees a stable shape regardless of schema drift.
  - Returning `{"error": ...}` rather than raising, so the loop keeps going.

To wire it up:
  1. Add a `db/` package to your app with the models below.
  2. Put a `session` and `project_id` into `ToolContext.extras` from your route
     handler (see `routes/agent.py`).
  3. Add `from app.agent.tools import meetings as _meetings` to
     `app/agent/tools/__init__.py`.

Originally extracted from work on a meeting-summarisation app. The models
(`Project`, `Meeting`, `Decision`, ...) are not part of this template.
"""

from __future__ import annotations

import json
from typing import Any

# These imports will fail in this template (no `db` package). Kept verbatim
# so the file reads like real production code when you go to wire it up.
#
# from sqlmodel import select
# from app.db.models import ActionItem, Decision, FileDoc, Highlight, Meeting

from app.agent.tools import ToolContext  # noqa: F401 — referenced in signatures


def _maybe_json(value: str | None) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


# @tool(
#     name="list_meetings",
#     description=(
#         "List meetings in the active project, newest first. "
#         "Use this to discover which meetings exist before fetching one."
#     ),
#     parameters={
#         "type": "object",
#         "properties": {
#             "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
#             "status": {"type": "string", "enum": ["recording", "processing", "ready", "failed"]},
#         },
#     },
# )
# async def list_meetings(ctx: ToolContext, limit: int = 10, status: str | None = None) -> dict[str, Any]:
#     session = ctx.extras["session"]
#     project_id = ctx.extras["project_id"]
#     stmt = select(Meeting).where(Meeting.project_id == project_id)
#     if status:
#         stmt = stmt.where(Meeting.status == status)
#     stmt = stmt.order_by(Meeting.recorded_at.desc()).limit(min(max(limit, 1), 50))
#     rows = (await session.exec(stmt)).all()
#     return {
#         "project_id": project_id,
#         "count": len(rows),
#         "meetings": [
#             {
#                 "id": m.id,
#                 "title": m.title,
#                 "type": m.type,
#                 "status": m.status,
#                 "recorded_at": m.recorded_at,
#                 "duration_sec": m.duration_sec,
#             }
#             for m in rows
#         ],
#     }
#
#
# @tool(
#     name="get_meeting",
#     description=(
#         "Fetch a meeting's metadata plus its decisions, action items, and "
#         "highlights. Call after list_meetings when the user asks about a "
#         "specific meeting."
#     ),
#     parameters={
#         "type": "object",
#         "required": ["meeting_id"],
#         "properties": {"meeting_id": {"type": "string"}},
#     },
# )
# async def get_meeting(ctx: ToolContext, meeting_id: str) -> dict[str, Any]:
#     session = ctx.extras["session"]
#     project_id = ctx.extras["project_id"]
#     meeting = (await session.exec(select(Meeting).where(Meeting.id == meeting_id))).first()
#     if meeting is None or meeting.project_id != project_id:
#         return {"error": f"meeting not found in active project: {meeting_id}"}
#     decisions = (await session.exec(select(Decision).where(Decision.meeting_id == meeting_id))).all()
#     actions = (await session.exec(select(ActionItem).where(ActionItem.meeting_id == meeting_id))).all()
#     highlights = (await session.exec(select(Highlight).where(Highlight.meeting_id == meeting_id))).all()
#     return {
#         "id": meeting.id,
#         "title": meeting.title,
#         "status": meeting.status,
#         "recorded_at": meeting.recorded_at,
#         "duration_sec": meeting.duration_sec,
#         "decisions": [
#             {
#                 "id": d.id,
#                 "statement": d.statement,
#                 "rationale": d.rationale,
#                 "status": d.status,
#                 "dissenters": _maybe_json(d.dissenters),
#             }
#             for d in decisions
#         ],
#         "action_items": [
#             {
#                 "id": a.id,
#                 "title": a.title,
#                 "owner": a.owner_speaker,
#                 "due_date": a.due_date,
#                 "priority": a.priority,
#                 "status": a.status,
#             }
#             for a in actions
#         ],
#         "highlights": [
#             {"id": h.id, "label": h.label, "start_ms": h.start_ms, "end_ms": h.end_ms}
#             for h in highlights
#         ],
#     }
#
#
# @tool(
#     name="get_master_doc",
#     description=(
#         "Return the project's compacted master document — the canonical "
#         "summary across all meetings. Prefer this for high-level questions."
#     ),
#     parameters={"type": "object", "properties": {}},
# )
# async def get_master_doc(ctx: ToolContext) -> dict[str, Any]:
#     session = ctx.extras["session"]
#     project_id = ctx.extras["project_id"]
#     doc = (
#         await session.exec(
#             select(FileDoc)
#             .where(FileDoc.project_id == project_id, FileDoc.kind == "master")
#             .order_by(FileDoc.version.desc())
#             .limit(1)
#         )
#     ).first()
#     if doc is None:
#         return {"available": False, "reason": "no master document for this project yet"}
#     return {
#         "available": True,
#         "version": doc.version,
#         "title": doc.title,
#         "content": doc.content,
#         "updated_at": doc.created_at,
#     }

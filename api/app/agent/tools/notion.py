"""Notion agent tools.

Returns mock payloads when NOTION_TOKEN is unset so the template runs without
external credentials. When set, hits the real Notion API.

Reference: https://developers.notion.com/reference/intro
"""

from __future__ import annotations

from typing import Any

import httpx

from app.agent.tools import tool
from app.config import get_settings

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


@tool(
    name="notion_search",
    description=(
        "Search the connected Notion workspace for pages or databases matching a query. "
        "Returns a mock result if NOTION_TOKEN is not configured."
    ),
    parameters={
        "type": "object",
        "required": ["query"],
        "properties": {
            "query": {"type": "string", "description": "Free-text query."},
            "filter_type": {
                "type": "string",
                "description": "Restrict results.",
                "enum": ["page", "database"],
            },
        },
    },
)
async def notion_search(query: str, filter_type: str | None = None) -> dict[str, Any]:
    token = get_settings().notion_token
    if not token:
        return {
            "configured": False,
            "note": "NOTION_TOKEN unset — returning mock data. Wire a token to hit the real API.",
            "results": [
                {
                    "id": "mock-page-id",
                    "type": "page",
                    "title": f"Mock result for: {query!r}",
                    "url": "https://www.notion.so/mock",
                }
            ],
        }

    body: dict[str, Any] = {"query": query, "page_size": 10}
    if filter_type:
        body["filter"] = {"value": filter_type, "property": "object"}

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(f"{NOTION_API}/search", headers=_headers(token), json=body)
        resp.raise_for_status()
        data = resp.json()

    return {
        "configured": True,
        "results": [
            {
                "id": item["id"],
                "type": item.get("object"),
                "title": _extract_title(item),
                "url": item.get("url"),
            }
            for item in data.get("results", [])
        ],
    }


@tool(
    name="notion_get_page",
    description=(
        "Fetch the block children of a Notion page (its rendered content). "
        "Returns a mock result if NOTION_TOKEN is not configured."
    ),
    parameters={
        "type": "object",
        "required": ["page_id"],
        "properties": {
            "page_id": {"type": "string", "description": "Notion page or block ID."},
        },
    },
)
async def notion_get_page(page_id: str) -> dict[str, Any]:
    token = get_settings().notion_token
    if not token:
        return {
            "configured": False,
            "note": "NOTION_TOKEN unset — returning mock data.",
            "page_id": page_id,
            "blocks": [
                {"type": "paragraph", "text": "This is a mock paragraph from a stubbed Notion page."}
            ],
        }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{NOTION_API}/blocks/{page_id}/children",
            headers=_headers(token),
            params={"page_size": 50},
        )
        resp.raise_for_status()
        data = resp.json()

    return {
        "configured": True,
        "page_id": page_id,
        "blocks": [_block_text(b) for b in data.get("results", [])],
    }


def _extract_title(item: dict[str, Any]) -> str:
    props = item.get("properties") or {}
    for prop in props.values():
        if prop.get("type") == "title":
            parts = prop.get("title") or []
            return "".join(p.get("plain_text", "") for p in parts) or "(untitled)"
    if "title" in item:
        return "".join(p.get("plain_text", "") for p in item["title"]) or "(untitled)"
    return "(untitled)"


def _block_text(block: dict[str, Any]) -> dict[str, Any]:
    btype = block.get("type", "unknown")
    payload = block.get(btype) or {}
    rich = payload.get("rich_text") or []
    text = "".join(part.get("plain_text", "") for part in rich)
    return {"type": btype, "text": text}

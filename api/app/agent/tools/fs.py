"""Filesystem agent tools — sandboxed to settings.content_root.

These exist so the template runs end-to-end out of the box. Drop a few files
into the content root and the agent can `list_folder` + `read_file` over them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.agent.tools import tool
from app.config import get_settings

MAX_READ_BYTES = 200_000


def _sandbox_root() -> Path:
    root = get_settings().content_root_path
    root.mkdir(parents=True, exist_ok=True)
    return root


def _resolve_inside_sandbox(path: str) -> Path:
    """Resolve `path` (relative or absolute) and ensure it stays inside the sandbox."""
    root = _sandbox_root()
    candidate = (root / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if root not in candidate.parents and candidate != root:
        raise ValueError(f"path escapes the sandbox: {path}")
    return candidate


@tool(
    name="list_folder",
    description=(
        "List files and subfolders inside the agent's content workspace. "
        "Use this to discover what's available before reading a specific file. "
        "Pass an empty path to list the root."
    ),
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Folder path relative to the workspace root. Empty = root.",
                "default": "",
            },
        },
    },
)
async def list_folder(path: str = "") -> dict[str, Any]:
    target = _resolve_inside_sandbox(path) if path else _sandbox_root()
    if not target.exists():
        return {"error": f"folder not found: {path}"}
    if not target.is_dir():
        return {"error": f"not a folder: {path}"}

    entries: list[dict[str, Any]] = []
    for child in sorted(target.iterdir()):
        if child.name.startswith("."):
            continue
        stat = child.stat()
        entries.append(
            {
                "name": child.name,
                "kind": "folder" if child.is_dir() else "file",
                "size": stat.st_size if child.is_file() else None,
                "path": str(child.relative_to(_sandbox_root())),
            }
        )
    return {"path": path or "", "count": len(entries), "entries": entries}


@tool(
    name="read_file",
    description=(
        "Read a UTF-8 text file from the content workspace. "
        f"Returns at most {MAX_READ_BYTES} bytes."
    ),
    parameters={
        "type": "object",
        "required": ["path"],
        "properties": {
            "path": {"type": "string", "description": "File path relative to the workspace root."},
        },
    },
)
async def read_file(path: str) -> dict[str, Any]:
    target = _resolve_inside_sandbox(path)
    if not target.exists():
        return {"error": f"file not found: {path}"}
    if not target.is_file():
        return {"error": f"not a file: {path}"}

    data = target.read_bytes()
    truncated = len(data) > MAX_READ_BYTES
    if truncated:
        data = data[:MAX_READ_BYTES]
    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError:
        return {"error": f"file is not utf-8 text: {path}", "size": target.stat().st_size}

    return {
        "path": path,
        "size": target.stat().st_size,
        "truncated": truncated,
        "content": content,
    }

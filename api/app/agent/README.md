# Chat agent (template)

A multi-turn, tool-using chat. The model picks tools at runtime instead of
having context preloaded.

## Layout

```
agent/
├── loop.py         # Tool-using loop. One Groq streaming call per turn.
├── prompts.py      # System prompt.
└── tools/
    ├── __init__.py # @tool decorator + Registry + ToolContext
    ├── fs.py       # list_folder, read_file (sandboxed to settings.content_root)
    ├── notion.py   # notion_search, notion_get_page (mock if NOTION_TOKEN unset)
    └── meetings.py # REFERENCE ONLY — DB-backed tool pattern, not registered
```

The HTTP entrypoint is `app/routes/agent.py` (POST `/agent`, SSE).

## How to add a tool

1. Create a module under `app/agent/tools/<your_module>.py`.
2. Define an async function decorated with `@tool(name, description, parameters)`
   — `parameters` is a JSON Schema object.
3. If the tool needs per-request state (DB session, user ID, etc.), accept a
   `ctx: ToolContext` keyword and read it from `ctx.extras`.
4. Import your module from `app/agent/tools/__init__.py` so it registers.

```python
from app.agent.tools import ToolContext, tool

@tool(
    name="count_words",
    description="Count words in a given string.",
    parameters={
        "type": "object",
        "required": ["text"],
        "properties": {"text": {"type": "string"}},
    },
)
async def count_words(text: str) -> dict:
    return {"count": len(text.split())}
```

For DB-backed tools, look at `tools/meetings.py` — that's the shape.

## Event types streamed to the client

| `type`        | `data` shape                                        |
| ------------- | --------------------------------------------------- |
| `text`        | `string` — partial assistant text                   |
| `tool_call`   | `{ id, name, args }` — model invoked a tool         |
| `tool_result` | `{ id, name, result }` — backend ran the tool       |
| `done`        | `{ iterations }` — model returned final answer      |
| `error`       | `{ message, iteration? }` — something blew up       |

## Configuration

- `GROQ_API_KEY` — required.
- `CONTENT_ROOT` — where the `fs` tools are allowed to look. Defaults to
  `./.workspace`. Anything outside the resolved root is rejected.
- `NOTION_TOKEN` — optional. Without it, `notion_*` tools return mock data.

## Open follow-ups

- No conversation persistence — every request starts fresh. Wire a DB / cache
  layer in the route if you want continuity beyond `history` round-tripping.
- Groq-only. The Gemini / OpenAI / Anthropic branches would go inside
  `loop.py` behind the same event shape.
- Streaming text inside a tool-calling turn is collected and yielded as a
  single `text` event for clarity. Live token streaming would need a worker
  thread → async queue bridge.

# chat-agent-template

A small reference scaffold for building a **tool-using chat agent** with:

- **Groq** (Llama 3.3 70B, OpenAI-compatible tool calling) as the model
- **FastAPI** backend with one streaming SSE endpoint (`POST /agent`)
- **Vite + React 19** frontend with a drop-in `<AgentChat />` panel that renders text + tool calls live
- A **pluggable tool registry** (`@tool` decorator → JSON-schema), with two example tools:
  - `list_folder` / `read_file` — sandboxed filesystem browser (works out of the box)
  - `notion_search` / `notion_get_page` — Notion API client, returns mock data if `NOTION_TOKEN` is unset

> **Status: incomplete.** This was extracted from work on a meeting-summarisation
> app where the actual chat feature ended up being much simpler (voice-to-text
> popup, not an agent). The scaffolding still works and is worth keeping for the
> next agent project. Things like persistence, auth, multi-provider support,
> and richer tool renderers are deliberately *not* here yet.

## Layout

```
chat-agent-template/
├── api/                          FastAPI backend
│   ├── app/
│   │   ├── main.py               Health + agent route registration
│   │   ├── config.py             Settings (GROQ_API_KEY, NOTION_TOKEN, content root)
│   │   ├── routes/agent.py       POST /agent — SSE
│   │   └── agent/
│   │       ├── loop.py           Multi-turn tool loop, Groq streaming
│   │       ├── prompts.py        System prompt
│   │       └── tools/
│   │           ├── __init__.py   @tool decorator + Registry + ToolContext
│   │           ├── fs.py         list_folder, read_file (sandboxed)
│   │           ├── notion.py     notion_search, notion_get_page
│   │           └── meetings.py   REFERENCE ONLY — Summit DB shape, not registered
│   ├── pyproject.toml
│   └── README.md
├── web/                          Vite + React 19 + TS strict
│   ├── src/
│   │   ├── App.tsx               Demo page mounting <AgentChat />
│   │   ├── main.tsx
│   │   ├── index.css             Minimal styles for the agent classes
│   │   └── components/agent/
│   │       ├── AgentChat.tsx     Streaming chat panel
│   │       ├── ToolCallCard.tsx  Collapsible tool inspector
│   │       ├── agent-client.ts   Typed SSE consumer
│   │       └── README.md
│   ├── index.html, vite.config.ts, tsconfig.json, package.json
├── .env.example
├── Makefile
└── README.md
```

## Quick start

```bash
# 1. set up env
cp .env.example .env       # add GROQ_API_KEY (required), NOTION_TOKEN (optional)

# 2. install + run
make bootstrap             # uv pip install api deps, bun install web deps
make dev                   # api on :8000, web on :5173
```

Open <http://localhost:5173>, ask something like:

> *"What files are in the workspace? Read the README."*

The agent will call `list_folder`, then `read_file`, then synthesise an answer.

## What's incomplete

- **No conversation persistence** — every page refresh starts fresh.
- **No auth** — assume `127.0.0.1`-only, single-user local dev.
- **No Gemini / OpenAI / Anthropic providers** — Groq only. The `loop.py` is the swap point; the event shape stays the same.
- **No real Notion integration tested** — code matches the public API shape but
  has only been exercised against the mock path.
- **`tools/meetings.py`** is kept as a reference for wiring DB-backed tools,
  but is *not* registered (would require a DB layer the template doesn't ship).
- **Minimal styling** — `index.css` has just enough to be legible. Treat as a
  blank canvas.

## Why a template

The agent shape (registry + JSON-schema tools + SSE event types: `text` /
`tool_call` / `tool_result` / `done` / `error`) is the part worth keeping. The
filesystem and Notion examples show two flavours of tool — local synchronous
vs. external HTTP — so the next tool you add has a precedent either way.

## License

MIT.

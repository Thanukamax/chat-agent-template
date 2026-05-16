# `<AgentChat />`

Drop-in chat panel that talks to `POST /agent` and renders a streaming
multi-turn conversation, including the agent's tool calls.

```tsx
import { AgentChat } from "@/components/agent/AgentChat";

export function DemoPage() {
  return <AgentChat projectId="demo" />;
}
```

## Files

```
agent/
├── AgentChat.tsx      Stateful chat panel
├── ToolCallCard.tsx   Collapsible {name, args, result} card
├── agent-client.ts    Typed SSE consumer (text | tool_call | tool_result | done | error)
└── README.md
```

## Event flow

1. User submits → optimistic user turn appended, empty assistant turn pushed.
2. `agent-client.ts` opens a `fetch` POST → SSE stream, decoded into typed `AgentEvent`s.
3. `text` events append to the assistant bubble; `tool_call` / `tool_result` mutate `ToolCallCard`s in place.
4. `done` (or `[DONE]`) ends the stream; `error` surfaces inline.

## Adding a custom tool renderer

`ToolCallCard` renders all tools generically. To give a tool a richer card,
branch on `name` either inside `AgentChat.tsx` or by extracting a
`<ToolCallRouter />`:

```tsx
function renderTool(t: ToolEvent) {
  if (t.name === "read_file" && t.result) return <FilePreview result={t.result} />;
  return <ToolCallCard {...t} />;
}
```

## Configuration

- `VITE_API_URL` — point at a non-default API origin (defaults to `/api`,
  which the Vite dev proxy maps to `:8000`).

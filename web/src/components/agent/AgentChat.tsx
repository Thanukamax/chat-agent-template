import { useCallback, useRef, useState } from "react";

import { agentStream, type AgentEvent, type AgentMessage } from "./agent-client";
import { ToolCallCard } from "./ToolCallCard";

interface AgentChatProps {
  projectId: string;
  placeholder?: string;
}

type ToolEvent = {
  id: string;
  name: string;
  args: Record<string, unknown>;
  result?: unknown;
  pending: boolean;
};

type Turn =
  | { kind: "user"; text: string }
  | { kind: "assistant"; text: string; tools: ToolEvent[] };

export function AgentChat({ projectId, placeholder = "Ask Summit anything…" }: AgentChatProps) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const turnsRef = useRef<Turn[]>([]);
  turnsRef.current = turns;

  const updateLastAssistant = useCallback((mutate: (turn: Turn & { kind: "assistant" }) => void) => {
    setTurns((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      if (last && last.kind === "assistant") mutate(last);
      return next;
    });
  }, []);

  const send = useCallback(async () => {
    const message = input.trim();
    if (!message || busy) return;

    const history: AgentMessage[] = turnsRef.current.flatMap<AgentMessage>((t) =>
      t.kind === "user"
        ? [{ role: "user", content: t.text }]
        : t.text
          ? [{ role: "assistant", content: t.text }]
          : [],
    );

    setInput("");
    setBusy(true);
    setTurns((prev) => [...prev, { kind: "user", text: message }, { kind: "assistant", text: "", tools: [] }]);

    try {
      for await (const ev of agentStream({ projectId, message, history })) {
        applyEvent(ev, updateLastAssistant);
      }
    } catch (err) {
      const reason = err instanceof Error ? err.message : String(err);
      updateLastAssistant((turn) => {
        turn.text = (turn.text ? `${turn.text}\n\n` : "") + `⚠ ${reason}`;
      });
    } finally {
      setBusy(false);
    }
  }, [busy, input, projectId, updateLastAssistant]);

  return (
    <div className="agent-chat">
      <div className="agent-log" role="log" aria-live="polite">
        {turns.map((turn, i) =>
          turn.kind === "user" ? (
            <div key={i} className="agent-turn agent-turn--user">
              <div className="agent-bubble">{turn.text}</div>
            </div>
          ) : (
            <div key={i} className="agent-turn agent-turn--assistant">
              {turn.tools.map((t) => (
                <ToolCallCard
                  key={t.id}
                  name={t.name}
                  args={t.args}
                  result={t.result}
                  pending={t.pending}
                />
              ))}
              {turn.text && <div className="agent-bubble">{turn.text}</div>}
            </div>
          ),
        )}
      </div>
      <div className="agent-composer">
        <input
          className="agent-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder={placeholder}
          disabled={busy}
        />
        <button className="agent-send" type="button" onClick={send} disabled={busy || !input.trim()}>
          {busy ? "…" : "Send"}
        </button>
      </div>
    </div>
  );
}

function applyEvent(
  ev: AgentEvent,
  updateLastAssistant: (mutate: (turn: Turn & { kind: "assistant" }) => void) => void,
): void {
  switch (ev.type) {
    case "text":
      updateLastAssistant((turn) => {
        turn.text += ev.data;
      });
      return;
    case "tool_call":
      updateLastAssistant((turn) => {
        turn.tools = [
          ...turn.tools,
          { id: ev.data.id, name: ev.data.name, args: ev.data.args, pending: true },
        ];
      });
      return;
    case "tool_result":
      updateLastAssistant((turn) => {
        turn.tools = turn.tools.map((t) =>
          t.id === ev.data.id ? { ...t, result: ev.data.result, pending: false } : t,
        );
      });
      return;
    case "error":
      updateLastAssistant((turn) => {
        turn.text = (turn.text ? `${turn.text}\n\n` : "") + `⚠ ${ev.data.message}`;
      });
      return;
    case "done":
      return;
  }
}

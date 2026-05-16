import { useState } from "react";

interface ToolCallCardProps {
  name: string;
  args: Record<string, unknown>;
  result?: unknown;
  pending?: boolean;
}

export function ToolCallCard({ name, args, result, pending = false }: ToolCallCardProps) {
  const [open, setOpen] = useState(false);
  const status = pending ? "running…" : result !== undefined ? "done" : "queued";

  return (
    <div className="tool-call-card" data-status={status}>
      <button
        type="button"
        className="tool-call-head"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className="tool-call-icon" aria-hidden>
          {pending ? "⏳" : result !== undefined ? "✓" : "•"}
        </span>
        <span className="tool-call-name">{name}</span>
        <span className="tool-call-status">{status}</span>
      </button>
      {open && (
        <div className="tool-call-body">
          <div className="tool-call-section">
            <div className="tool-call-label">args</div>
            <pre className="tool-call-json">{JSON.stringify(args, null, 2)}</pre>
          </div>
          {result !== undefined && (
            <div className="tool-call-section">
              <div className="tool-call-label">result</div>
              <pre className="tool-call-json">{JSON.stringify(result, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

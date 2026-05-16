/**
 * Streaming client for POST /agent (SSE).
 *
 * Mirrors the `chatStream` helper in `src/lib/api.ts` but yields *typed events*
 * (text / tool_call / tool_result / done / error) so the UI can render tool
 * activity, not just text chunks.
 */

const RAW = (import.meta.env["VITE_API_URL"] ?? "/api") as string;
const BASE = RAW.replace(/\/$/, "");

export type AgentMessage = { role: "user" | "assistant"; content: string };

export type AgentEvent =
  | { type: "text"; data: string }
  | { type: "tool_call"; data: { id: string; name: string; args: Record<string, unknown> } }
  | { type: "tool_result"; data: { id: string; name: string; result: unknown } }
  | { type: "done"; data: { iterations: number } }
  | { type: "error"; data: { message: string; iteration?: number } };

export interface AgentRequest {
  projectId: string;
  message: string;
  history?: AgentMessage[];
}

export async function* agentStream(req: AgentRequest): AsyncGenerator<AgentEvent> {
  const res = await fetch(`${BASE}/agent`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_id: req.projectId,
      message: req.message,
      history: req.history,
    }),
  });
  if (!res.ok || !res.body) throw new Error(`Agent failed: ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const payload = line.slice(6).trim();
      if (!payload || payload === "[DONE]") {
        if (payload === "[DONE]") return;
        continue;
      }
      try {
        yield JSON.parse(payload) as AgentEvent;
      } catch {
        // Malformed SSE frame — skip rather than abort the stream.
      }
    }
  }
}

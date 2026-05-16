import { AgentChat } from "./components/agent/AgentChat";

export function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>chat-agent-template</h1>
        <p className="app-tagline">
          Try: <em>"list the files in the workspace and tell me what you see"</em>
        </p>
      </header>
      <main className="app-main">
        <AgentChat projectId="demo" />
      </main>
    </div>
  );
}

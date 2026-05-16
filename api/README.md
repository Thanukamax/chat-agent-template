# api

FastAPI backend. One real endpoint: `POST /agent` (SSE).

```bash
uv pip install -e .
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/docs
```

## Endpoints

| Method | Path     | Notes                                                   |
| ------ | -------- | ------------------------------------------------------- |
| GET    | `/`      | Service info                                            |
| GET    | `/health`| Liveness                                                |
| POST   | `/agent` | SSE stream, see `app/agent/README.md` for event shapes  |

## Smoke test the stream

```bash
curl -N -X POST http://localhost:8000/agent \
  -H 'content-type: application/json' \
  -d '{"message":"List the files in the workspace and tell me what you see."}'
```

You should see a sequence of SSE `data:` frames containing
`{type: "tool_call"}`, `{type: "tool_result"}`, `{type: "text"}`,
`{type: "done"}`.

"""Chat agent template — minimal FastAPI app."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="chat-agent-template",
    version=__version__,
    description="Reference scaffold for a tool-using chat agent (Groq + FastAPI).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routes.agent import router as agent_router  # noqa: E402

app.include_router(agent_router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {"name": "chat-agent-template", "version": __version__}

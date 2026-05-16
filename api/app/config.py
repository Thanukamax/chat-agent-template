from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8000

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Model
    groq_api_key: str | None = None

    # Tool: filesystem sandbox
    content_root: str = "./.workspace"

    # Tool: Notion (optional)
    notion_token: str | None = None

    @property
    def content_root_path(self) -> Path:
        return Path(self.content_root).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

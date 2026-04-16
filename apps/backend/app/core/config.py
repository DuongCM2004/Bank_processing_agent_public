from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="OPS_AGENT_",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Ops Agent Backend"
    env: str = "local"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

    log_level: str = "INFO"
    log_json: bool = False

    postgres_dsn: str = "postgresql+psycopg://ops_agent:ops_agent@localhost:5432/ops_agent"
    db_echo: bool = False
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_pre_ping: bool = True

    redis_url: str = "redis://localhost:6379/0"
    task_queue_name: str = "ops-agent-default"

    ai_provider_mode: str = "placeholder"
    ai_provider_endpoint: str | None = None
    ai_provider_timeout_seconds: int = 30

    storage_backend: str = "local"
    storage_root_path: Path = Path(".runtime/uploads")
    max_upload_bytes: int = 15 * 1024 * 1024
    allowed_upload_mime_types: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["application/pdf", "image/png", "image/jpeg"]
    )

    @field_validator("cors_origins", "allowed_upload_mime_types", mode="before")
    @classmethod
    def parse_csv_list(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseModel):
    v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=list)


class DatabaseSettings(BaseModel):
    dsn: PostgresDsn
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_pre_ping: bool = True


class LoggingSettings(BaseModel):
    level: str = "INFO"
    json_logs: bool = False


class WorkerSettings(BaseModel):
    redis_url: str = "redis://localhost:6379/0"
    task_queue_name: str = "ops-agent-default"


class AIIntegrationSettings(BaseModel):
    provider_mode: Literal["placeholder", "disabled", "external"] = "placeholder"


class ProcessingSettings(BaseModel):
    max_retry_attempts: int = 3
    min_ocr_confidence: float = 0.75
    min_extraction_confidence: float = 0.8


class StorageSettings(BaseModel):
    backend: Literal["local", "blob_placeholder"] = "local"
    root_path: Path = Path("./.runtime/uploads")
    max_upload_bytes: int = 15 * 1024 * 1024
    allowed_mime_types: list[str] = Field(
        default_factory=lambda: ["application/pdf", "image/png", "image/jpeg"]
    )


class FeatureFlags(BaseModel):
    enable_db_healthcheck: bool = True


class AppSettings(BaseSettings):
    app_name: str = "Ops Agent Backend"
    env: Literal["local", "test", "staging", "production"] = "local"
    debug: bool = False

    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=list)

    postgres_dsn: PostgresDsn = Field(
        default="postgresql+psycopg://ops_agent:ops_agent@localhost:5432/ops_agent"
    )
    db_echo: bool = False
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_pre_ping: bool = True

    log_level: str = "INFO"
    log_json: bool = False

    redis_url: str = "redis://localhost:6379/0"
    task_queue_name: str = "ops-agent-default"
    ai_provider_mode: Literal["placeholder", "disabled", "external"] = "placeholder"
    processing_max_retry_attempts: int = 3
    processing_min_ocr_confidence: float = 0.75
    processing_min_extraction_confidence: float = 0.8
    storage_backend: Literal["local", "blob_placeholder"] = "local"
    storage_root_path: Path = Path("./.runtime/uploads")
    max_upload_bytes: int = 15 * 1024 * 1024
    allowed_upload_mime_types: list[str] = Field(
        default_factory=lambda: ["application/pdf", "image/png", "image/jpeg"]
    )
    enable_db_healthcheck: bool = True

    model_config = SettingsConfigDict(
        env_prefix="OPS_AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def api(self) -> ApiSettings:
        return ApiSettings(v1_prefix=self.api_v1_prefix, cors_origins=self.cors_origins)

    @property
    def database(self) -> DatabaseSettings:
        return DatabaseSettings(
            dsn=self.postgres_dsn,
            echo=self.db_echo,
            pool_size=self.db_pool_size,
            max_overflow=self.db_max_overflow,
            pool_pre_ping=self.db_pool_pre_ping,
        )

    @property
    def logging(self) -> LoggingSettings:
        return LoggingSettings(level=self.log_level, json_logs=self.log_json)

    @property
    def worker(self) -> WorkerSettings:
        return WorkerSettings(redis_url=self.redis_url, task_queue_name=self.task_queue_name)

    @property
    def ai(self) -> AIIntegrationSettings:
        return AIIntegrationSettings(provider_mode=self.ai_provider_mode)

    @property
    def processing(self) -> ProcessingSettings:
        return ProcessingSettings(
            max_retry_attempts=self.processing_max_retry_attempts,
            min_ocr_confidence=self.processing_min_ocr_confidence,
            min_extraction_confidence=self.processing_min_extraction_confidence,
        )

    @property
    def storage(self) -> StorageSettings:
        return StorageSettings(
            backend=self.storage_backend,
            root_path=self.storage_root_path,
            max_upload_bytes=self.max_upload_bytes,
            allowed_mime_types=self.allowed_upload_mime_types,
        )

    @property
    def features(self) -> FeatureFlags:
        return FeatureFlags(enable_db_healthcheck=self.enable_db_healthcheck)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()

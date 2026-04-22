from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class ApiSettings(BaseModel):
    v1_prefix: str = "/api/v1"
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)


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
    provider_mode: Literal["placeholder", "disabled", "external", "gpt"] = "placeholder"
    provider_endpoint: str | None = None
    provider_api_key: str | None = Field(default=None, repr=False)
    provider_timeout_seconds: int = 30
    openai_api_key: str | None = Field(default=None, repr=False)
    gpt_model: str = "gpt-4.1"
    openai_store_response: bool = False
    llm_prompt_version: str = "identity-document-extraction-v1"
    llm_schema_version: str = "identity-document-v1"
    image_max_dimension_px: int = 1600
    image_jpeg_quality: int = 90


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
    blob_endpoint: str | None = None
    blob_bucket: str | None = None
    kms_key_id: str | None = None


class FeatureFlags(BaseModel):
    enable_db_healthcheck: bool = True


class AppSettings(BaseSettings):
    app_name: str = "Ops Agent Backend"
    env: Literal["local", "test", "development", "staging", "production"] = "local"
    debug: bool = False

    api_v1_prefix: str = "/api/v1"
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

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
    ai_provider_mode: Literal["placeholder", "disabled", "external", "gpt"] = "placeholder"
    ai_provider_endpoint: str | None = None
    ai_provider_api_key: str | None = Field(default=None, repr=False)
    ai_provider_timeout_seconds: int = 30
    openai_api_key: str | None = Field(default=None, repr=False)
    gpt_model: str = "gpt-4.1"
    openai_store_response: bool = False
    llm_prompt_version: str = "identity-document-extraction-v1"
    llm_schema_version: str = "identity-document-v1"
    image_max_dimension_px: int = 1600
    image_jpeg_quality: int = 90
    processing_max_retry_attempts: int = 3
    processing_min_ocr_confidence: float = 0.75
    processing_min_extraction_confidence: float = 0.8
    storage_backend: Literal["local", "blob_placeholder"] = "local"
    storage_root_path: Path = Path("./.runtime/uploads")
    max_upload_bytes: int = 15 * 1024 * 1024
    allowed_upload_mime_types: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["application/pdf", "image/png", "image/jpeg"]
    )
    storage_blob_endpoint: str | None = None
    storage_blob_bucket: str | None = None
    storage_kms_key_id: str | None = None
    enable_db_healthcheck: bool = True

    model_config = SettingsConfigDict(
        env_prefix="OPS_AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_origins", "allowed_upload_mime_types", mode="before")
    @classmethod
    def parse_csv_list(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]

        return value

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
        return AIIntegrationSettings(
            provider_mode=self.ai_provider_mode,
            provider_endpoint=self.ai_provider_endpoint,
            provider_api_key=self.ai_provider_api_key,
            provider_timeout_seconds=self.ai_provider_timeout_seconds,
            openai_api_key=self.openai_api_key or self.ai_provider_api_key,
            gpt_model=self.gpt_model,
            openai_store_response=self.openai_store_response,
            llm_prompt_version=self.llm_prompt_version,
            llm_schema_version=self.llm_schema_version,
            image_max_dimension_px=self.image_max_dimension_px,
            image_jpeg_quality=self.image_jpeg_quality,
        )

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
            blob_endpoint=self.storage_blob_endpoint,
            blob_bucket=self.storage_blob_bucket,
            kms_key_id=self.storage_kms_key_id,
        )

    @property
    def features(self) -> FeatureFlags:
        return FeatureFlags(enable_db_healthcheck=self.enable_db_healthcheck)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()

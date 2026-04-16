from __future__ import annotations

from ops_agent.config import AppSettings


def test_settings_expose_structured_views() -> None:
    settings = AppSettings(
        api_v1_prefix="/api/v1",
        cors_origins="http://localhost:5173,http://localhost:3000",
        postgres_dsn="postgresql+psycopg://ops_agent:ops_agent@localhost:5432/ops_agent",
        redis_url="redis://localhost:6379/1",
        ai_provider_mode="external",
        ai_provider_endpoint="https://ai-provider.example.test",
        ai_provider_api_key="placeholder-secret",
        allowed_upload_mime_types="application/pdf,image/png",
        storage_blob_endpoint="https://blob.example.test",
        storage_blob_bucket="ops-agent-documents",
    )

    assert settings.api.v1_prefix == "/api/v1"
    assert settings.api.cors_origins == ["http://localhost:5173", "http://localhost:3000"]
    assert str(settings.database.dsn).startswith("postgresql+psycopg://")
    assert settings.worker.task_queue_name == "ops-agent-default"
    assert settings.ai.provider_mode == "external"
    assert settings.ai.provider_endpoint == "https://ai-provider.example.test"
    assert settings.storage.allowed_mime_types == ["application/pdf", "image/png"]
    assert settings.storage.blob_bucket == "ops-agent-documents"


def test_settings_parse_csv_lists_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("OPS_AGENT_CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    monkeypatch.setenv("OPS_AGENT_ALLOWED_UPLOAD_MIME_TYPES", "application/pdf,image/png,image/jpeg")

    settings = AppSettings()

    assert settings.api.cors_origins == ["http://localhost:5173", "http://localhost:3000"]
    assert settings.storage.allowed_mime_types == ["application/pdf", "image/png", "image/jpeg"]

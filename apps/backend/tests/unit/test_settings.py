from __future__ import annotations

from ops_agent.config import AppSettings


def test_settings_expose_structured_views() -> None:
    settings = AppSettings(
        api_v1_prefix="/api/v1",
        postgres_dsn="postgresql+psycopg://ops_agent:ops_agent@localhost:5432/ops_agent",
        redis_url="redis://localhost:6379/1",
        ai_provider_mode="placeholder",
    )

    assert settings.api.v1_prefix == "/api/v1"
    assert str(settings.database.dsn).startswith("postgresql+psycopg://")
    assert settings.worker.task_queue_name == "ops-agent-default"
    assert settings.ai.provider_mode == "placeholder"


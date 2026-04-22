from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from alembic import context
from alembic.config import Config


def test_alembic_ini_uses_clean_revision_structure() -> None:
    config = Config("alembic.ini")

    assert config.get_main_option("script_location") == "alembic"
    assert config.get_main_option("prepend_sys_path") == "src"
    assert config.get_main_option("file_template") == "%(rev)s_%(slug)s"
    assert config.get_main_option("timezone") == "UTC"
    assert config.get_main_option("version_locations").endswith("/alembic/versions")


def test_alembic_env_get_url_returns_plain_string(monkeypatch) -> None:
    monkeypatch.setattr(context, "config", SimpleNamespace(config_file_name=None), raising=False)
    namespace: dict[str, object] = {"__name__": "alembic_env_test"}
    source = Path("alembic/env.py").read_text(encoding="utf-8")
    exec(source.split("if context.is_offline_mode():", maxsplit=1)[0], namespace)

    url = namespace["get_url"]()

    assert isinstance(url, str)
    assert url.startswith("postgresql+psycopg://")


def test_initial_migration_revision_file_exists() -> None:
    versions_dir = Path("alembic/versions")
    initial_migration = versions_dir / "20260415_0001_initial_backend_schema.py"

    assert versions_dir.exists()
    assert initial_migration.exists()

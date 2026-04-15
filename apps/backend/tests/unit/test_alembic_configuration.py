from __future__ import annotations

from configparser import RawConfigParser
from pathlib import Path


def test_alembic_ini_uses_clean_revision_structure() -> None:
    config = RawConfigParser()
    config.read(Path("alembic.ini"), encoding="utf-8")

    assert config.get("alembic", "script_location") == "alembic"
    assert config.get("alembic", "file_template") == "%(rev)s_%(slug)s"
    assert config.get("alembic", "timezone") == "UTC"
    assert config.get("alembic", "version_locations") == "%(here)s/alembic/versions"


def test_initial_migration_revision_file_exists() -> None:
    versions_dir = Path("alembic/versions")
    initial_migration = versions_dir / "20260415_0001_initial_backend_schema.py"

    assert versions_dir.exists()
    assert initial_migration.exists()

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_json_schemas_are_valid_json_documents() -> None:
    schema_dir = ROOT / "contracts" / "jsonschema"
    assert schema_dir.exists()

    for path in schema_dir.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert payload["type"] == "object"


def test_openapi_draft_exists() -> None:
    openapi_path = ROOT / "openapi" / "ops-agent-v1.yaml"
    text = openapi_path.read_text(encoding="utf-8")

    assert "openapi: 3.1.0" in text
    assert "/v1/cases:" in text
    assert "/internal/workflows/start:" in text


def test_api_contract_pack_exists() -> None:
    contract_pack_path = ROOT / "openapi" / "ops-agent-contract-pack.yaml"
    text = contract_pack_path.read_text(encoding="utf-8")

    assert "openapi: 3.1.0" in text
    assert "x-ops-agent-state-guards:" in text
    assert "components:" in text


def test_api_contract_pack_notes_exist() -> None:
    notes_path = ROOT / "docs" / "api-contract-pack.md"
    text = notes_path.read_text(encoding="utf-8")

    assert "State-Safe Validation Pattern" in text
    assert "Future Code Generation Notes" in text


def test_migration_pack_readme_and_hardening_migration_exist() -> None:
    readme_path = ROOT / "db" / "migrations" / "README.md"
    migration_path = ROOT / "db" / "migrations" / "0006_status_constraints_and_indexes.sql"

    readme_text = readme_path.read_text(encoding="utf-8")
    migration_text = migration_path.read_text(encoding="utf-8")

    assert "Migration Order" in readme_text
    assert "Status Typing Approach" in readme_text
    assert "ALTER TABLE ops_core.cases" in migration_text
    assert "CREATE INDEX IF NOT EXISTS idx_outbox_events_pending" in migration_text

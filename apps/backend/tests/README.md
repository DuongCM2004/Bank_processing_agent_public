# Backend Test Scaffold

This test scaffold is organized to keep fast feedback loops for unit tests while still supporting API-level integration coverage for the MVP workflow.

Structure:

- `tests/conftest.py`: shared app, settings, database, and API client fixtures
- `tests/fixtures/`: reusable payload builders and ORM seed helpers
- `tests/unit/`: fast service, schema, workflow, and route-focused tests
- `tests/integration/`: end-to-end API tests against the FastAPI app and test database
- `tests/contract/`: reserved for OpenAPI or consumer-contract checks

Database strategy:

- Default: in-memory SQLite via `sqlite+pysqlite:///:memory:`
- Optional override: set `OPS_AGENT_TEST_DATABASE_URL` to point to another test database, including PostgreSQL
- The schema is created and dropped per test, which keeps tests isolated and simple for the MVP stage

Shared fixtures:

- `test_settings`: app settings configured for test mode and isolated upload storage
- `db_engine`: SQLAlchemy engine for the active test database strategy
- `db_session_factory`: session factory bound to the test engine
- `db_session`: isolated database session with metadata lifecycle management
- `test_app`: FastAPI app with test dependency overrides
- `api_client` / `client`: `TestClient` bound to the test app
- builders in `tests/fixtures/builders.py` for common payloads and seeded review cases

Typical commands from `apps/backend`:

```powershell
py -m pytest tests/unit -q -p no:cacheprovider
py -m pytest tests/integration -q -p no:cacheprovider
py -m pytest tests -q -p no:cacheprovider
```

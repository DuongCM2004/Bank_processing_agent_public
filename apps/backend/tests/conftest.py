from __future__ import annotations

from collections.abc import Generator
import os
from pathlib import Path
import shutil
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from ops_agent.app import create_app
from ops_agent.api.dependencies import get_app_settings
from ops_agent.config import AppSettings, get_settings
from ops_agent.domain.shared.enums import RoleCode
from ops_agent.infrastructure.db.base import Base
from ops_agent.infrastructure.db import models as db_models  # noqa: F401
from ops_agent.infrastructure.db.session import get_db_session
from ops_agent.security.rbac import Principal, get_current_principal


DEFAULT_TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"


def _resolve_test_database_url() -> str:
    return os.getenv("OPS_AGENT_TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)


def _test_database_backend(database_url: str) -> str:
    if database_url.startswith("sqlite"):
        return "sqlite"
    if database_url.startswith("postgresql"):
        return "postgresql"
    return "custom"


@pytest.fixture(scope="session")
def test_database_url() -> str:
    return _resolve_test_database_url()


@pytest.fixture(scope="session")
def test_database_backend(test_database_url: str) -> str:
    return _test_database_backend(test_database_url)


@pytest.fixture(scope="session")
def test_database_strategy(test_database_backend: str) -> str:
    if test_database_backend == "sqlite":
        return "in_memory_sqlite"
    if test_database_backend == "postgresql":
        return "external_postgresql"
    return "external_database"


@pytest.fixture
def test_settings() -> AppSettings:
    upload_root = Path(".runtime") / "test-uploads" / uuid4().hex
    # `_env_file=None` prevents pydantic-settings from merging the repo-root
    # `.env` (which is tuned for the ID-card demo and narrows mime types).
    # Tests should depend only on the defaults + explicit kwargs below.
    settings = AppSettings(
        _env_file=None,
        env="test",
        debug=False,
        postgres_dsn="postgresql+psycopg://ops_agent:ops_agent@localhost:5432/ops_agent_test",
        storage_root_path=upload_root,
        enable_db_healthcheck=True,
    )
    yield settings
    shutil.rmtree(upload_root, ignore_errors=True)


@pytest.fixture
def db_engine(test_database_url: str, test_database_backend: str):
    engine_kwargs: dict[str, object] = {"future": True}
    if test_database_backend == "sqlite":
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        engine_kwargs["poolclass"] = StaticPool

    engine = create_engine(
        test_database_url,
        **engine_kwargs,
    )
    yield engine
    engine.dispose()


@pytest.fixture
def db_session_factory(db_engine):
    TestingSessionLocal = sessionmaker(bind=db_engine, autocommit=False, autoflush=False, class_=Session)
    return TestingSessionLocal


@pytest.fixture
def db_session(db_engine, db_session_factory) -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=db_engine)
    session = db_session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=db_engine)


@pytest.fixture
def test_app(test_settings: AppSettings, db_session: Session):
    app = create_app(settings=test_settings)

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_app_settings] = lambda: test_settings
    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[get_current_principal] = lambda: Principal(
        subject="test-admin",
        roles=frozenset({RoleCode.ADMIN}),
        display_name="Test Admin",
    )

    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def api_client(test_app) -> Generator[TestClient, None, None]:
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture
def client(api_client: TestClient) -> TestClient:
    return api_client

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from ops_agent.app import create_app
from ops_agent.api.dependencies import get_app_settings
from ops_agent.config import AppSettings, get_settings
from ops_agent.infrastructure.db.base import Base
from ops_agent.infrastructure.db import models as db_models  # noqa: F401
from ops_agent.infrastructure.db.session import get_db_session


TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"


@pytest.fixture
def test_settings() -> AppSettings:
    upload_root = Path(".runtime") / "test-uploads" / uuid4().hex
    return AppSettings(
        env="test",
        debug=False,
        postgres_dsn="postgresql+psycopg://ops_agent:ops_agent@localhost:5432/ops_agent_test",
        storage_root_path=upload_root,
        enable_db_healthcheck=True,
    )


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        TEST_DATABASE_URL,
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(test_settings: AppSettings, db_session: Session) -> Generator[TestClient, None, None]:
    app = create_app(settings=test_settings)

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_app_settings] = lambda: test_settings
    app.dependency_overrides[get_db_session] = lambda: db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

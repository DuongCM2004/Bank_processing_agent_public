from __future__ import annotations

from functools import lru_cache
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ops_agent.config import AppSettings, get_settings


def build_engine(settings: AppSettings):
    return create_engine(
        str(settings.database.dsn),
        echo=settings.database.echo,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        pool_pre_ping=settings.database.pool_pre_ping,
        future=True,
    )


@lru_cache(maxsize=1)
def get_engine():
    return build_engine(get_settings())


@lru_cache(maxsize=1)
def get_session_factory():
    return sessionmaker(bind=get_engine(), autocommit=False, autoflush=False, class_=Session)


def get_db_session() -> Iterator[Session]:
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ops_agent.api.error_handlers import register_exception_handlers
from ops_agent.api.router import api_router
from ops_agent.config import AppSettings, get_settings
from ops_agent.infrastructure.logging.setup import configure_logging


def build_lifespan(settings: AppSettings):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(settings)
        app.state.settings = settings
        yield

    return lifespan


def create_app(settings: AppSettings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    app = FastAPI(
        title=app_settings.app_name,
        version="0.1.0",
        debug=app_settings.debug,
        openapi_url=f"{app_settings.api.v1_prefix}/openapi.json",
        docs_url=f"{app_settings.api.v1_prefix}/docs",
        redoc_url=f"{app_settings.api.v1_prefix}/redoc",
        lifespan=build_lifespan(app_settings),
    )

    if app_settings.api.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in app_settings.api.cors_origins],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=app_settings.api.v1_prefix)
    return app

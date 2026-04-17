from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError, app_error_handler
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
    )
    app.add_exception_handler(AppError, app_error_handler)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/", tags=["system"], include_in_schema=False)
    def root() -> dict[str, object]:
        api_base = settings.api_v1_prefix.rstrip("/")
        return {
            "name": settings.app_name,
            "status": "ok",
            "environment": settings.env,
            "api_base": api_base,
            "links": {
                "health": f"{api_base}/health",
                "docs": f"{api_base}/docs",
                "openapi": f"{api_base}/openapi.json",
            },
            "features": [
                "case creation and listing",
                "case status transitions",
                "document upload and listing",
                "processing queue dispatch",
                "extraction result recording",
                "decision recording",
                "manual review action recording",
                "case audit event listing",
            ],
        }

    return app


app = create_app()

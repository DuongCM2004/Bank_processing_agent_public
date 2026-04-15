from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ops_agent.domain.shared.exceptions import OpsAgentError

logger = logging.getLogger(__name__)


def _trace_id(request: Request) -> str:
    header_trace_id = request.headers.get("x-trace-id")
    return header_trace_id or str(uuid4())


def _validation_details(exc: RequestValidationError) -> list[dict[str, object]]:
    details: list[dict[str, object]] = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", ()))
        details.append(
            {
                "field": location or None,
                "issue": error.get("msg", "Invalid value."),
                "context": error.get("ctx", {}),
            }
        )
    return details


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(OpsAgentError)
    async def handle_ops_agent_error(request: Request, exc: OpsAgentError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "trace_id": _trace_id(request),
                    "details": [],
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "request_validation_failed",
                    "message": "Request validation failed.",
                    "trace_id": _trace_id(request),
                    "details": _validation_details(exc),
                }
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application error", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected error occurred.",
                    "trace_id": _trace_id(request),
                    "details": [],
                }
            },
        )

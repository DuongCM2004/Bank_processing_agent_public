from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ops_agent.domain.errors import DomainError
from ops_agent.models import ErrorResponse


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        trace_id = uuid4().hex
        payload = ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            trace_id=trace_id,
            retryable=exc.retryable,
            details=exc.details or None,
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        if getattr(exc, "status_code", None):
            trace_id = uuid4().hex
            payload = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
            payload.setdefault("trace_id", trace_id)
            payload.setdefault("retryable", False)
            return JSONResponse(status_code=exc.status_code, content=payload)

        trace_id = uuid4().hex
        payload = ErrorResponse(
            error_code="internal_server_error",
            message="The request could not be completed.",
            trace_id=trace_id,
            retryable=False,
        )
        return JSONResponse(status_code=500, content=payload.model_dump(mode="json"))

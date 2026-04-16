from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import audit, cases, decisions, documents, health, manual_review, processing

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(cases.router)
api_router.include_router(documents.router)
api_router.include_router(processing.router)
api_router.include_router(decisions.router)
api_router.include_router(manual_review.router)
api_router.include_router(audit.router)


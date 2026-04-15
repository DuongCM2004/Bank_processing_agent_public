from __future__ import annotations

from fastapi import APIRouter

from ops_agent.api.routes.audit import router as audit_router
from ops_agent.api.routes.cases import router as cases_router
from ops_agent.api.routes.decisions import router as decisions_router
from ops_agent.api.routes.documents import router as documents_router
from ops_agent.api.routes.health import router as health_router
from ops_agent.api.routes.manual_review import router as manual_review_router

api_router = APIRouter()
api_router.include_router(audit_router)
api_router.include_router(cases_router)
api_router.include_router(decisions_router)
api_router.include_router(documents_router)
api_router.include_router(health_router)
api_router.include_router(manual_review_router)

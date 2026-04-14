from __future__ import annotations

from fastapi import FastAPI

from ops_agent.api.dependencies import repository, workflow_service
from ops_agent.api.error_handlers import register_error_handlers
from ops_agent.api.routes.audit import router as audit_router
from ops_agent.api.routes.cases import router as cases_router
from ops_agent.api.routes.internal_workflows import router as internal_workflows_router
from ops_agent.api.routes.review_tasks import router as review_tasks_router
from ops_agent.api.routes.system import router as system_router

app = FastAPI(
    title="Bank Document Processing Agent API",
    version="0.1.0",
    description="MVP backend foundation for secure banking document workflow orchestration.",
)

service = workflow_service

register_error_handlers(app)
app.include_router(system_router)
app.include_router(cases_router)
app.include_router(review_tasks_router)
app.include_router(audit_router)
app.include_router(internal_workflows_router)

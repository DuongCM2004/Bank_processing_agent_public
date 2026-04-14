from __future__ import annotations

from fastapi import APIRouter, Depends

from ops_agent.api.dependencies import get_case_application_service
from ops_agent.application.services.case_application_service import CaseApplicationService
from ops_agent.models import AuditEventListResponse

router = APIRouter(tags=["audit"])


@router.get("/v1/cases/{case_id}/audit-events", response_model=AuditEventListResponse)
def list_audit_events(
    case_id: str,
    service: CaseApplicationService = Depends(get_case_application_service),
) -> AuditEventListResponse:
    return AuditEventListResponse(items=list(service.list_audit_events(case_id)))

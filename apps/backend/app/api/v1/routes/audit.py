from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import AuditServiceDep
from app.schemas.audit import AuditEventListResponse
from app.security.rbac import Permission, require_permission

router = APIRouter(prefix="/cases/{case_id}/audit-events", tags=["audit"])


@router.get(
    "",
    response_model=AuditEventListResponse,
    dependencies=[Depends(require_permission(Permission.AUDIT_READ))],
)
def list_case_audit_events(
    case_id: UUID,
    service: AuditServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> AuditEventListResponse:
    return service.list_case_events(case_id, limit=limit, offset=offset)


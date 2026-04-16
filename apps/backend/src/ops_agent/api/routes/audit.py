from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from ops_agent.api.dependencies import AuditServiceDep
from ops_agent.api.openapi import error_responses
from ops_agent.api.schemas import AuditEventListResponse
from ops_agent.domain.shared.enums import AuditActorType, AuditEventType
from ops_agent.security.rbac import Permission, require_permission

router = APIRouter(prefix="/cases/{case_id}/audit-events", tags=["audit-events"])


@router.get(
    "",
    response_model=AuditEventListResponse,
    status_code=status.HTTP_200_OK,
    summary="List case audit events",
    description="Lists structured audit events for a case with optional filters by event type, actor type, and target resource type.",
    operation_id="listCaseAuditEvents",
    responses=error_responses(401, 403, 404, 422, 500),
    dependencies=[Depends(require_permission(Permission.AUDIT_READ))],
)
def list_case_audit_events(
    case_id: UUID,
    audit_service: AuditServiceDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    event_type: AuditEventType | None = Query(default=None),
    actor_type: AuditActorType | None = Query(default=None),
    resource_type: str | None = Query(default=None, min_length=1, max_length=80),
) -> AuditEventListResponse:
    return audit_service.list_case_events(
        case_id=case_id,
        limit=limit,
        offset=offset,
        event_type=event_type,
        actor_type=actor_type,
        resource_type=resource_type,
    )

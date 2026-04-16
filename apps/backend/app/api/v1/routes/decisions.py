from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import DecisionServiceDep
from app.schemas.decisions import DecisionCreateRequest, DecisionResponse
from app.security.rbac import Permission, require_permission

router = APIRouter(prefix="/cases/{case_id}/decisions", tags=["decisions"])


@router.post(
    "",
    response_model=DecisionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.DECISION_CREATE))],
)
def create_decision(
    case_id: UUID,
    request: DecisionCreateRequest,
    service: DecisionServiceDep,
) -> DecisionResponse:
    return service.create_decision(case_id=case_id, request=request)


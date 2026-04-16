from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import CaseServiceDep
from app.models.enums import CaseStatus
from app.schemas.cases import (
    CaseCreateRequest,
    CaseListResponse,
    CaseResponse,
    CaseStatusTransitionRequest,
    CaseStatusTransitionResponse,
)
from app.security.rbac import Permission, require_permission

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post(
    "",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.CASE_CREATE))],
)
def create_case(request: CaseCreateRequest, service: CaseServiceDep) -> CaseResponse:
    return service.create_case(request)


@router.get(
    "",
    response_model=CaseListResponse,
    dependencies=[Depends(require_permission(Permission.CASE_READ))],
)
def list_cases(
    service: CaseServiceDep,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: CaseStatus | None = Query(default=None, alias="status"),
    current_queue: str | None = Query(default=None, max_length=80),
    case_type: str | None = Query(default=None, max_length=80),
) -> CaseListResponse:
    return service.list_cases(
        limit=limit,
        offset=offset,
        status=status_filter,
        current_queue=current_queue,
        case_type=case_type,
    )


@router.get(
    "/{case_id}",
    response_model=CaseResponse,
    dependencies=[Depends(require_permission(Permission.CASE_READ))],
)
def get_case(case_id: UUID, service: CaseServiceDep) -> CaseResponse:
    return CaseResponse.model_validate(service.get_case(case_id))


@router.patch(
    "/{case_id}/status",
    response_model=CaseStatusTransitionResponse,
    dependencies=[Depends(require_permission(Permission.CASE_STATUS_UPDATE))],
)
def transition_case_status(
    case_id: UUID,
    request: CaseStatusTransitionRequest,
    service: CaseServiceDep,
) -> CaseStatusTransitionResponse:
    return service.transition_case(case_id=case_id, request=request)


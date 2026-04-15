from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status

from ops_agent.api.dependencies import CaseManagementServiceDep
from ops_agent.api.schemas import (
    CaseCreateRequest,
    CaseCreateResponse,
    CaseDetailResponse,
    CaseListResponse,
    CaseSummaryResponse,
    UpdateCaseStatusRequest,
    UpdateCaseStatusResponse,
)
from ops_agent.domain.shared.enums import CaseStatus

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseCreateResponse, status_code=status.HTTP_201_CREATED)
def create_case(request: CaseCreateRequest, case_service: CaseManagementServiceDep) -> CaseCreateResponse:
    return case_service.create_case(request)


@router.get("", response_model=CaseListResponse, status_code=status.HTTP_200_OK)
def list_cases(
    case_service: CaseManagementServiceDep,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: CaseStatus | None = Query(default=None, alias="status"),
    current_queue: str | None = Query(default=None, max_length=80),
    case_type: str | None = Query(default=None, max_length=80),
) -> CaseListResponse:
    return case_service.list_cases(
        limit=limit,
        offset=offset,
        status=status_filter,
        current_queue=current_queue,
        case_type=case_type,
    )


@router.get("/{case_id}", response_model=CaseSummaryResponse, status_code=status.HTTP_200_OK)
def get_case(case_id: UUID, case_service: CaseManagementServiceDep) -> CaseSummaryResponse:
    return case_service.get_case(case_id)


@router.get("/{case_id}/detail", response_model=CaseDetailResponse, status_code=status.HTTP_200_OK)
def get_case_detail(case_id: UUID, case_service: CaseManagementServiceDep) -> CaseDetailResponse:
    return case_service.get_case_detail(case_id)


@router.patch("/{case_id}/status", response_model=UpdateCaseStatusResponse, status_code=status.HTTP_200_OK)
def update_case_status(
    case_id: UUID,
    request: UpdateCaseStatusRequest,
    case_service: CaseManagementServiceDep,
) -> UpdateCaseStatusResponse:
    return case_service.update_case_status(case_id=case_id, request=request)

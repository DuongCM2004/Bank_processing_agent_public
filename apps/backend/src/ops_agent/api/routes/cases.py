from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from ops_agent.api.dependencies import CaseManagementServiceDep
from ops_agent.api.openapi import error_responses
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
from ops_agent.security.rbac import Permission, require_permission

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post(
    "",
    response_model=CaseCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create case",
    description="Creates a new case and optionally registers initial document metadata supplied during intake.",
    operation_id="createCase",
    responses=error_responses(400, 401, 403, 409, 422, 500),
    dependencies=[Depends(require_permission(Permission.CASE_CREATE))],
)
def create_case(request: CaseCreateRequest, case_service: CaseManagementServiceDep) -> CaseCreateResponse:
    return case_service.create_case(request)


@router.get(
    "",
    response_model=CaseListResponse,
    status_code=status.HTTP_200_OK,
    summary="List cases",
    description="Lists cases for operations users with pagination and optional status or queue filters.",
    operation_id="listCases",
    responses=error_responses(401, 403, 422, 500),
    dependencies=[Depends(require_permission(Permission.CASE_READ))],
)
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


@router.get(
    "/{case_id}",
    response_model=CaseSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get case summary",
    description="Returns the top-level case summary used for list-to-detail navigation.",
    operation_id="getCase",
    responses=error_responses(401, 403, 404, 422, 500),
    dependencies=[Depends(require_permission(Permission.CASE_READ))],
)
def get_case(case_id: UUID, case_service: CaseManagementServiceDep) -> CaseSummaryResponse:
    return case_service.get_case(case_id)


@router.get(
    "/{case_id}/detail",
    response_model=CaseDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get case detail",
    description="Returns a frontend-ready case detail view including linked documents, processing results, findings, decisions, manual review actions, and audit events.",
    operation_id="getCaseDetail",
    responses=error_responses(401, 403, 404, 422, 500),
    dependencies=[Depends(require_permission(Permission.CASE_READ))],
)
def get_case_detail(case_id: UUID, case_service: CaseManagementServiceDep) -> CaseDetailResponse:
    return case_service.get_case_detail(case_id)


@router.patch(
    "/{case_id}/status",
    response_model=UpdateCaseStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Update case status",
    description="Applies an explicit case workflow transition through the safe workflow service. Direct status mutation is not supported.",
    operation_id="updateCaseStatus",
    responses=error_responses(401, 403, 404, 409, 422, 500),
    dependencies=[Depends(require_permission(Permission.CASE_STATUS_UPDATE))],
)
def update_case_status(
    case_id: UUID,
    request: UpdateCaseStatusRequest,
    case_service: CaseManagementServiceDep,
) -> UpdateCaseStatusResponse:
    return case_service.update_case_status(case_id=case_id, request=request)

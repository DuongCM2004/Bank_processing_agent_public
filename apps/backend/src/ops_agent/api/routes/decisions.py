from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from ops_agent.api.dependencies import DecisionServiceDep
from ops_agent.api.openapi import error_responses
from ops_agent.api.schemas import DecisionActionRequest, DecisionCreateRequest, DecisionWorkflowResponse
from ops_agent.security.rbac import Permission, require_permission

router = APIRouter(prefix="/cases/{case_id}/decisions", tags=["decisions"])


@router.post(
    "",
    response_model=DecisionWorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create decision",
    description="Creates an explicit decision record for a case and applies the corresponding safe workflow transition.",
    operation_id="createDecision",
    responses=error_responses(401, 403, 404, 409, 422, 500),
    dependencies=[Depends(require_permission(Permission.DECISION_WRITE))],
)
def create_decision(
    case_id: UUID,
    request: DecisionCreateRequest,
    decision_service: DecisionServiceDep,
) -> DecisionWorkflowResponse:
    return decision_service.create_decision(case_id=case_id, request=request)


@router.post(
    "/approve",
    response_model=DecisionWorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve case",
    description="Records an approval decision for a decision-ready case through the decision service.",
    operation_id="approveCase",
    responses=error_responses(401, 403, 404, 409, 422, 500),
    dependencies=[Depends(require_permission(Permission.DECISION_WRITE))],
)
def approve_case(
    case_id: UUID,
    request: DecisionActionRequest,
    decision_service: DecisionServiceDep,
) -> DecisionWorkflowResponse:
    return decision_service.approve_case(case_id=case_id, request=request)


@router.post(
    "/reject",
    response_model=DecisionWorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject case",
    description="Records a rejection decision for a decision-ready case through the decision service.",
    operation_id="rejectCase",
    responses=error_responses(401, 403, 404, 409, 422, 500),
    dependencies=[Depends(require_permission(Permission.DECISION_WRITE))],
)
def reject_case(
    case_id: UUID,
    request: DecisionActionRequest,
    decision_service: DecisionServiceDep,
) -> DecisionWorkflowResponse:
    return decision_service.reject_case(case_id=case_id, request=request)


@router.post(
    "/request-review",
    response_model=DecisionWorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Request more review",
    description="Records a decision outcome that routes the case back into manual review.",
    operation_id="requestMoreReview",
    responses=error_responses(401, 403, 404, 409, 422, 500),
    dependencies=[Depends(require_permission(Permission.DECISION_WRITE))],
)
def request_more_review(
    case_id: UUID,
    request: DecisionActionRequest,
    decision_service: DecisionServiceDep,
) -> DecisionWorkflowResponse:
    return decision_service.request_more_review(case_id=case_id, request=request)

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from ops_agent.api.dependencies import DecisionServiceDep
from ops_agent.api.schemas import DecisionActionRequest, DecisionCreateRequest, DecisionWorkflowResponse

router = APIRouter(prefix="/cases/{case_id}/decisions", tags=["decisions"])


@router.post("", response_model=DecisionWorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_decision(
    case_id: UUID,
    request: DecisionCreateRequest,
    decision_service: DecisionServiceDep,
) -> DecisionWorkflowResponse:
    return decision_service.create_decision(case_id=case_id, request=request)


@router.post("/approve", response_model=DecisionWorkflowResponse, status_code=status.HTTP_200_OK)
def approve_case(
    case_id: UUID,
    request: DecisionActionRequest,
    decision_service: DecisionServiceDep,
) -> DecisionWorkflowResponse:
    return decision_service.approve_case(case_id=case_id, request=request)


@router.post("/reject", response_model=DecisionWorkflowResponse, status_code=status.HTTP_200_OK)
def reject_case(
    case_id: UUID,
    request: DecisionActionRequest,
    decision_service: DecisionServiceDep,
) -> DecisionWorkflowResponse:
    return decision_service.reject_case(case_id=case_id, request=request)


@router.post("/request-review", response_model=DecisionWorkflowResponse, status_code=status.HTTP_200_OK)
def request_more_review(
    case_id: UUID,
    request: DecisionActionRequest,
    decision_service: DecisionServiceDep,
) -> DecisionWorkflowResponse:
    return decision_service.request_more_review(case_id=case_id, request=request)

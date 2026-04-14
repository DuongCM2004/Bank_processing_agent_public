from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ops_agent.api.dependencies import get_case_application_service
from ops_agent.application.services.case_application_service import CaseApplicationService
from ops_agent.models import ReviewTaskClaimRequest, ReviewTaskListResponse, ReviewTaskRecord

router = APIRouter(prefix="/v1/review-tasks", tags=["review-tasks"])


@router.get("", response_model=ReviewTaskListResponse)
def list_review_tasks(
    status: str | None = Query(default=None),
    service: CaseApplicationService = Depends(get_case_application_service),
) -> ReviewTaskListResponse:
    return service.list_review_tasks(status_filter=status)


@router.post("/{task_id}/claim", response_model=ReviewTaskRecord)
def claim_review_task(
    task_id: str,
    request: ReviewTaskClaimRequest,
    service: CaseApplicationService = Depends(get_case_application_service),
) -> ReviewTaskRecord:
    return service.claim_review_task(task_id, request)

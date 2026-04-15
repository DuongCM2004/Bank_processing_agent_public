from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from ops_agent.api.dependencies import ManualReviewServiceDep
from ops_agent.api.schemas import (
    ManualCorrectionSubmissionRequest,
    ManualCorrectionSubmissionResponse,
    ManualReviewActionResponse,
    ManualReviewNoteRequest,
    ManualReviewResubmitRequest,
    ManualReviewWorkflowResponse,
    RequireManualReviewRequest,
)

router = APIRouter(prefix="/cases/{case_id}/manual-review", tags=["manual-review"])


@router.post("/require", response_model=ManualReviewWorkflowResponse, status_code=status.HTTP_200_OK)
def require_manual_review(
    case_id: UUID,
    request: RequireManualReviewRequest,
    review_service: ManualReviewServiceDep,
) -> ManualReviewWorkflowResponse:
    return review_service.require_manual_review(case_id=case_id, request=request)


@router.post("/notes", response_model=ManualReviewActionResponse, status_code=status.HTTP_201_CREATED)
def add_manual_review_note(
    case_id: UUID,
    request: ManualReviewNoteRequest,
    review_service: ManualReviewServiceDep,
) -> ManualReviewActionResponse:
    return review_service.add_reviewer_note(case_id=case_id, request=request)


@router.post("/corrections", response_model=ManualCorrectionSubmissionResponse, status_code=status.HTTP_200_OK)
def submit_manual_corrections(
    case_id: UUID,
    request: ManualCorrectionSubmissionRequest,
    review_service: ManualReviewServiceDep,
) -> ManualCorrectionSubmissionResponse:
    return review_service.submit_corrections(case_id=case_id, request=request)


@router.post("/resubmit", response_model=ManualReviewWorkflowResponse, status_code=status.HTTP_200_OK)
def resubmit_manual_review_case(
    case_id: UUID,
    request: ManualReviewResubmitRequest,
    review_service: ManualReviewServiceDep,
) -> ManualReviewWorkflowResponse:
    return review_service.resubmit_case(case_id=case_id, request=request)

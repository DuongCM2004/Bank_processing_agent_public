from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from ops_agent.api.dependencies import ManualReviewServiceDep
from ops_agent.api.openapi import error_responses
from ops_agent.api.schemas import (
    ManualCorrectionSubmissionRequest,
    ManualCorrectionSubmissionResponse,
    ManualReviewActionResponse,
    ManualReviewNoteRequest,
    ManualReviewResubmitRequest,
    ManualReviewWorkflowResponse,
    RequireManualReviewRequest,
)
from ops_agent.security.rbac import Permission, require_permission

router = APIRouter(prefix="/cases/{case_id}/manual-review", tags=["manual-review"])


@router.post(
    "/require",
    response_model=ManualReviewWorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Require manual review",
    description="Routes a case into manual review and records the reviewer escalation action.",
    operation_id="requireManualReview",
    responses=error_responses(401, 403, 404, 409, 422, 500),
    dependencies=[Depends(require_permission(Permission.MANUAL_REVIEW_WRITE))],
)
def require_manual_review(
    case_id: UUID,
    request: RequireManualReviewRequest,
    review_service: ManualReviewServiceDep,
) -> ManualReviewWorkflowResponse:
    return review_service.require_manual_review(case_id=case_id, request=request)


@router.post(
    "/notes",
    response_model=ManualReviewActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add manual review note",
    description="Records a reviewer note as an explicit manual review action.",
    operation_id="addManualReviewNote",
    responses=error_responses(401, 403, 404, 409, 422, 500),
    dependencies=[Depends(require_permission(Permission.MANUAL_REVIEW_WRITE))],
)
def add_manual_review_note(
    case_id: UUID,
    request: ManualReviewNoteRequest,
    review_service: ManualReviewServiceDep,
) -> ManualReviewActionResponse:
    return review_service.add_reviewer_note(case_id=case_id, request=request)


@router.post(
    "/corrections",
    response_model=ManualCorrectionSubmissionResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit manual corrections",
    description="Applies reviewer corrections to extracted values while preserving before/after traceability and auditability.",
    operation_id="submitManualCorrections",
    responses=error_responses(401, 403, 404, 409, 422, 500),
    dependencies=[Depends(require_permission(Permission.MANUAL_REVIEW_WRITE))],
)
def submit_manual_corrections(
    case_id: UUID,
    request: ManualCorrectionSubmissionRequest,
    review_service: ManualReviewServiceDep,
) -> ManualCorrectionSubmissionResponse:
    return review_service.submit_corrections(case_id=case_id, request=request)


@router.post(
    "/resubmit",
    response_model=ManualReviewWorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Resubmit case after manual review",
    description="Resubmits a manually reviewed case back into the workflow for either decisioning or reprocessing.",
    operation_id="resubmitManualReviewCase",
    responses=error_responses(401, 403, 404, 409, 422, 500),
    dependencies=[Depends(require_permission(Permission.MANUAL_REVIEW_WRITE))],
)
def resubmit_manual_review_case(
    case_id: UUID,
    request: ManualReviewResubmitRequest,
    review_service: ManualReviewServiceDep,
) -> ManualReviewWorkflowResponse:
    return review_service.resubmit_case(case_id=case_id, request=request)

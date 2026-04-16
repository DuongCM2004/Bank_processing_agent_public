from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import ManualReviewServiceDep
from app.schemas.manual_review import ManualReviewActionCreateRequest, ManualReviewActionResponse
from app.security.rbac import Permission, require_permission

router = APIRouter(prefix="/cases/{case_id}/manual-review/actions", tags=["manual-review"])


@router.post(
    "",
    response_model=ManualReviewActionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.MANUAL_REVIEW_CREATE))],
)
def record_manual_review_action(
    case_id: UUID,
    request: ManualReviewActionCreateRequest,
    service: ManualReviewServiceDep,
) -> ManualReviewActionResponse:
    return service.record_action(case_id=case_id, request=request)


from __future__ import annotations

from uuid import UUID

from app.audit.logger import AuditLogger
from app.core.exceptions import NotFoundError
from app.models.enums import AuditActorType, AuditEventType, CaseStatus, ManualReviewActionType
from app.models.manual_review import ManualReviewAction
from app.repositories.cases import CaseRepository
from app.repositories.manual_review import ManualReviewRepository
from app.schemas.cases import CaseStatusTransitionRequest
from app.schemas.manual_review import ManualReviewActionCreateRequest, ManualReviewActionResponse
from app.services.cases import CaseService


class ManualReviewService:
    def __init__(
        self,
        review_repository: ManualReviewRepository,
        case_repository: CaseRepository,
        case_service: CaseService,
        audit_logger: AuditLogger,
    ) -> None:
        self.review_repository = review_repository
        self.case_repository = case_repository
        self.case_service = case_service
        self.audit_logger = audit_logger

    def record_action(
        self,
        *,
        case_id: UUID,
        request: ManualReviewActionCreateRequest,
    ) -> ManualReviewActionResponse:
        case = self.case_repository.get(case_id)
        if case is None:
            raise NotFoundError("Case not found.", error_code="case_not_found")
        action = ManualReviewAction(
            case_id=case_id,
            document_id=request.document_id,
            action_type=request.action_type,
            reviewer_id=request.reviewer_id,
            comment=request.comment,
            payload=request.payload,
            evidence_refs=[item.model_dump(mode="json") for item in request.evidence_refs],
            created_by=request.reviewer_id,
            updated_by=request.reviewer_id,
        )
        self.review_repository.add(action)
        self.review_repository.db.flush()
        self.audit_logger.record(
            event_type=AuditEventType.MANUAL_REVIEW_ACTION_RECORDED,
            actor_type=AuditActorType.USER,
            actor_id=request.reviewer_id,
            case_id=case_id,
            entity_type="manual_review_action",
            entity_id=action.id,
            message="Manual review action recorded.",
            details={"action_type": request.action_type.value},
        )
        self.review_repository.db.commit()
        self.review_repository.db.refresh(action)

        if request.action_type == ManualReviewActionType.REQUEST_REPROCESSING:
            self.case_service.transition_case(
                case_id=case_id,
                request=CaseStatusTransitionRequest(
                    to_status=CaseStatus.QUEUED_FOR_PROCESSING,
                    actor_id=request.reviewer_id,
                    reason_code="manual_reprocessing_requested",
                    comment=request.comment,
                ),
            )
        return ManualReviewActionResponse.model_validate(action)

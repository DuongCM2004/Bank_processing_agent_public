from __future__ import annotations

from uuid import UUID

from app.audit.logger import AuditLogger
from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.enums import AuditActorType, AuditEventType, CaseStatus, DocumentStatus, ManualReviewActionType
from app.models.manual_review import ManualReviewAction
from app.repositories.cases import CaseRepository
from app.repositories.documents import DocumentRepository, ProcessingResultRepository
from app.repositories.manual_review import ManualReviewRepository
from app.schemas.cases import CaseStatusTransitionRequest
from app.schemas.documents import DocumentReviewRequest, DocumentReviewResponse
from app.schemas.manual_review import ManualReviewActionCreateRequest, ManualReviewActionResponse
from app.schemas.processing import IdentityDocumentExtraction
from app.services.cases import CaseService


class ManualReviewService:
    def __init__(
        self,
        review_repository: ManualReviewRepository,
        document_repository: DocumentRepository,
        result_repository: ProcessingResultRepository,
        case_repository: CaseRepository,
        case_service: CaseService,
        audit_logger: AuditLogger,
    ) -> None:
        self.review_repository = review_repository
        self.document_repository = document_repository
        self.result_repository = result_repository
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

    def review_document(self, *, document_id: UUID, request: DocumentReviewRequest) -> DocumentReviewResponse:
        document = self.document_repository.get(document_id)
        if document is None:
            raise NotFoundError("Document not found.", error_code="document_not_found")
        extraction = self.result_repository.get_latest_extraction_for_document(document_id)
        reviewed_payload = self._resolve_reviewed_payload(request, extraction.extracted_payload if extraction else None)

        action_type = {
            "edit": ManualReviewActionType.CORRECT_DATA,
            "approve": ManualReviewActionType.APPROVE,
            "reject": ManualReviewActionType.REJECT,
        }[request.action]
        payload = {
            "review_action": request.action,
            "extraction_uuid": str(extraction.id) if extraction else None,
            "reviewed_payload": reviewed_payload,
            "diff": self._diff(extraction.extracted_payload if extraction else {}, reviewed_payload or {}),
        }
        action = ManualReviewAction(
            case_id=document.case_id,
            document_id=document.id,
            action_type=action_type,
            reviewer_id=request.reviewer_id,
            comment=request.comment,
            payload=payload,
            evidence_refs=[],
            created_by=request.reviewer_id,
            updated_by=request.reviewer_id,
        )
        self.review_repository.add(action)
        self.review_repository.db.flush()
        audit_event, audit_message = self._apply_review_action(
            request=request,
            document=document,
            extraction=extraction,
            reviewed_payload=reviewed_payload,
        )
        document.updated_by = request.reviewer_id
        self.audit_logger.record(
            event_type=audit_event,
            actor_type=AuditActorType.USER,
            actor_id=request.reviewer_id,
            case_id=document.case_id,
            entity_type="document",
            entity_id=document.id,
            message=audit_message,
            details={
                "action_type": action_type.value,
                "manual_review_action_uuid": str(action.id),
                "extraction_uuid": str(extraction.id) if extraction else None,
            },
        )
        self.review_repository.db.commit()
        self.review_repository.db.refresh(action)
        self.document_repository.db.refresh(document)
        return DocumentReviewResponse(
            document_uuid=document.id,
            extraction_uuid=extraction.id if extraction else None,
            status=document.status,
            action_id=action.id,
        )

    def _apply_review_action(
        self,
        *,
        request: DocumentReviewRequest,
        document: object,
        extraction: object | None,
        reviewed_payload: dict[str, object] | None,
    ) -> tuple[AuditEventType, str]:
        """Mutate document status and return the audit event and message for the given review action."""
        from app.models.document import Document as DocumentModel
        from app.models.document import ExtractionResult as ExtractionModel

        assert isinstance(document, DocumentModel)
        if request.action == "reject":
            document.status = DocumentStatus.REJECTED
            return AuditEventType.DOCUMENT_REJECTED, "Document extraction rejected during manual review."
        if request.action == "approve":
            if reviewed_payload is None:
                raise ValidationAppError("reviewed_payload is required to approve extracted data.")
            assert extraction is None or isinstance(extraction, ExtractionModel)
            document.document_metadata = {
                **(document.document_metadata or {}),
                "approved_extraction": reviewed_payload,
                "approved_extraction_uuid": str(extraction.id) if extraction else None,
            }
            document.status = DocumentStatus.PERSISTED
            return AuditEventType.DOCUMENT_PERSISTED, "Approved document extraction persisted to document metadata."
        # action == "edit"
        if reviewed_payload is None:
            raise ValidationAppError("reviewed_payload is required to save manual edits.")
        document.status = DocumentStatus.IN_REVIEW
        return AuditEventType.MANUAL_REVIEW_ACTION_RECORDED, "Document extraction edited during manual review."

    @staticmethod
    def _resolve_reviewed_payload(
        request: DocumentReviewRequest,
        extracted_payload: dict[str, object] | None,
    ) -> dict[str, object] | None:
        if request.reviewed_payload is not None:
            return request.reviewed_payload.model_dump(mode="json")
        if request.action != "approve" or extracted_payload is None:
            return None
        return IdentityDocumentExtraction.model_validate(extracted_payload).model_dump(mode="json")

    @staticmethod
    def _diff(before: dict[str, object], after: dict[str, object]) -> dict[str, dict[str, object | None]]:
        return {
            key: {"before": before.get(key), "after": after.get(key)}
            for key in sorted(set(before) | set(after))
            if before.get(key) != after.get(key)
        }

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from ops_agent.api.schemas import (
    EvidenceReferenceResponse,
    ManualCorrectionSubmissionRequest,
    ManualCorrectionSubmissionResponse,
    ManualReviewActionResponse,
    ManualReviewCorrectionFieldResponse,
    ManualReviewNoteRequest,
    ManualReviewResubmitRequest,
    ManualReviewWorkflowResponse,
    RequireManualReviewRequest,
)
from ops_agent.application.services.audit import AuditService
from ops_agent.application.services.case_workflow import CaseWorkflowService
from ops_agent.domain.shared.enums import (
    AuditActorType,
    CaseStatus,
    DocumentStatus,
    ManualReviewActionType,
)
from ops_agent.domain.shared.exceptions import ConflictError, ResourceNotFoundError
from ops_agent.domain.workflow import CaseTransitionContext
from ops_agent.infrastructure.db.models import Document, ExtractionResult, ManualReviewAction
from ops_agent.infrastructure.db.repositories.manual_review_repository import ManualReviewRepository


class ManualReviewService:
    def __init__(
        self,
        *,
        repository: ManualReviewRepository,
        workflow_service: CaseWorkflowService,
        audit_service: AuditService,
    ) -> None:
        self._repository = repository
        self._workflow_service = workflow_service
        self._audit_service = audit_service

    def require_manual_review(self, *, case_id: UUID, request: RequireManualReviewRequest) -> ManualReviewWorkflowResponse:
        case = self._get_case(case_id)
        document = self._get_document_if_supplied(case_id=case_id, document_id=request.document_id)
        occurred_at = datetime.now(UTC)
        previous_status = case.status

        if case.status != CaseStatus.MANUAL_REVIEW_REQUIRED:
            self._workflow_service.transition(
                case=case,
                to_status=CaseStatus.MANUAL_REVIEW_REQUIRED,
                context=CaseTransitionContext(
                    actor_type=AuditActorType.USER,
                    actor_id=str(request.performed_by_user_id),
                    reason_code=request.reason_code,
                    comment=request.comment,
                    metadata={"document_id": str(request.document_id) if request.document_id else None},
                    occurred_at=occurred_at,
                ),
            )
        self._set_review_status(document=document, occurred_at=occurred_at, actor_id=str(request.performed_by_user_id))

        action = self._create_action(
            case_id=case.id,
            document_id=request.document_id,
            performed_by_user_id=request.performed_by_user_id,
            action_type=ManualReviewActionType.ESCALATE,
            comment=request.comment,
            payload={
                "reason_code": request.reason_code,
                "previous_status": previous_status.value,
                "target_status": CaseStatus.MANUAL_REVIEW_REQUIRED.value,
            },
            evidence_refs=request.evidence_refs,
            occurred_at=occurred_at,
        )
        self._repository.commit()
        self._repository.refresh(case)
        self._repository.refresh(action)
        return self._to_workflow_response(case_status=case.status, status_changed_at=case.status_changed_at, case_id=case.id, action=action)

    def add_reviewer_note(self, *, case_id: UUID, request: ManualReviewNoteRequest) -> ManualReviewActionResponse:
        self._ensure_reviewable_status(case_id)
        self._get_document_if_supplied(case_id=case_id, document_id=request.document_id)
        action = self._create_action(
            case_id=case_id,
            document_id=request.document_id,
            performed_by_user_id=request.performed_by_user_id,
            action_type=ManualReviewActionType.ADD_NOTE,
            comment=request.comment,
            payload={"note_recorded": True},
            evidence_refs=request.evidence_refs,
            occurred_at=datetime.now(UTC),
        )
        self._repository.commit()
        self._repository.refresh(action)
        return self._to_action_response(action)

    def submit_corrections(self, *, case_id: UUID, request: ManualCorrectionSubmissionRequest) -> ManualCorrectionSubmissionResponse:
        case = self._ensure_reviewable_status(case_id)
        self._get_document_if_supplied(case_id=case_id, document_id=request.document_id)
        occurred_at = datetime.now(UTC)
        correction_records: list[dict[str, object]] = []
        correction_responses: list[ManualReviewCorrectionFieldResponse] = []

        for correction in request.corrections:
            extraction_result = self._get_extraction_result(case_id=case_id, extraction_result_id=correction.extraction_result_id)
            previous_value = extraction_result.extracted_payload.get(correction.field_name)
            if correction.before_value != previous_value:
                raise ConflictError(
                    f"Correction for field '{correction.field_name}' does not match the current stored value.",
                    error_code="manual_correction_stale_value",
                )
            extraction_result.extracted_payload = {
                **extraction_result.extracted_payload,
                correction.field_name: correction.after_value,
            }
            extraction_result.updated_at = occurred_at
            extraction_result.updated_by = str(request.performed_by_user_id)
            record = {
                "extraction_result_id": str(correction.extraction_result_id),
                "field_name": correction.field_name,
                "before_value": correction.before_value,
                "after_value": correction.after_value,
                    "evidence_refs": [ref.model_dump(mode="json") for ref in correction.evidence_refs],
                }
            correction_records.append(record)
            correction_responses.append(
                ManualReviewCorrectionFieldResponse(
                    extraction_result_id=correction.extraction_result_id,
                    field_name=correction.field_name,
                    before_value=correction.before_value,
                    after_value=correction.after_value,
                    evidence_refs=[EvidenceReferenceResponse.model_validate(ref.model_dump(mode="json")) for ref in correction.evidence_refs],
                )
            )

        action = self._create_action(
            case_id=case.id,
            document_id=request.document_id,
            performed_by_user_id=request.performed_by_user_id,
            action_type=ManualReviewActionType.CORRECT_DATA,
            comment=request.comment,
            payload={"corrections": correction_records},
            evidence_refs=request.evidence_refs,
            occurred_at=occurred_at,
        )
        self._repository.commit()
        self._repository.refresh(action)
        self._repository.refresh(case)
        return ManualCorrectionSubmissionResponse(
            case_id=case.id,
            case_status=case.status,
            status_changed_at=case.status_changed_at,
            corrections=correction_responses,
            action=self._to_action_response(action),
        )

    def resubmit_case(self, *, case_id: UUID, request: ManualReviewResubmitRequest) -> ManualReviewWorkflowResponse:
        case = self._ensure_reviewable_status(case_id)
        document = self._get_document_if_supplied(case_id=case_id, document_id=request.document_id)
        if request.target_status not in {CaseStatus.DECISION_READY, CaseStatus.QUEUED_FOR_PROCESSING}:
            raise ConflictError(
                "Manual review resubmission target must be 'decision_ready' or 'queued_for_processing'.",
                error_code="invalid_manual_review_target_status",
            )

        occurred_at = datetime.now(UTC)
        action_type = (
            ManualReviewActionType.REQUEST_REPROCESSING
            if request.target_status == CaseStatus.QUEUED_FOR_PROCESSING
            else ManualReviewActionType.CONFIRM_EXTRACTION
        )
        action = self._create_action(
            case_id=case.id,
            document_id=request.document_id,
            performed_by_user_id=request.performed_by_user_id,
            action_type=action_type,
            comment=request.comment,
            payload={
                "target_status": request.target_status.value,
                "reason_code": request.reason_code or self._default_reason_code_for_target(request.target_status),
            },
            evidence_refs=request.evidence_refs,
            occurred_at=occurred_at,
        )

        self._workflow_service.transition(
            case=case,
            to_status=request.target_status,
            context=CaseTransitionContext(
                actor_type=AuditActorType.USER,
                actor_id=str(request.performed_by_user_id),
                reason_code=request.reason_code or self._default_reason_code_for_target(request.target_status),
                comment=request.comment,
                metadata={"document_id": str(request.document_id) if request.document_id else None},
                occurred_at=occurred_at,
            ),
        )
        if request.target_status == CaseStatus.DECISION_READY:
            self._clear_review_status(document=document, occurred_at=occurred_at, actor_id=str(request.performed_by_user_id))

        self._repository.commit()
        self._repository.refresh(case)
        self._repository.refresh(action)
        return self._to_workflow_response(case_status=case.status, status_changed_at=case.status_changed_at, case_id=case.id, action=action)

    def _ensure_reviewable_status(self, case_id: UUID):
        case = self._get_case(case_id)
        if case.status != CaseStatus.MANUAL_REVIEW_REQUIRED:
            raise ConflictError(
                f"Case '{case_id}' is not currently in manual review.",
                error_code="case_not_in_manual_review",
            )
        return case

    def _get_case(self, case_id: UUID):
        case = self._repository.get_case_by_id(case_id)
        if case is None:
            raise ResourceNotFoundError("Case", str(case_id))
        return case

    def _get_document_if_supplied(self, *, case_id: UUID, document_id: UUID | None) -> Document | None:
        if document_id is None:
            return None
        document = self._repository.get_document_by_id(case_id, document_id)
        if document is None:
            raise ResourceNotFoundError("Document", str(document_id))
        return document

    def _get_extraction_result(self, *, case_id: UUID, extraction_result_id: UUID) -> ExtractionResult:
        extraction_result = self._repository.get_extraction_result_by_id(case_id, extraction_result_id)
        if extraction_result is None:
            raise ResourceNotFoundError("ExtractionResult", str(extraction_result_id))
        return extraction_result

    def _create_action(
        self,
        *,
        case_id: UUID,
        document_id: UUID | None,
        performed_by_user_id: UUID,
        action_type: ManualReviewActionType,
        comment: str | None,
        payload: dict[str, object],
        evidence_refs,
        occurred_at: datetime,
    ) -> ManualReviewAction:
        action = ManualReviewAction(
            case_id=case_id,
            document_id=document_id,
            performed_by_user_id=performed_by_user_id,
            action_type=action_type,
            comment=comment,
            payload=payload,
            evidence_refs=[ref.model_dump(mode="json") for ref in evidence_refs],
            created_by=str(performed_by_user_id),
            updated_by=str(performed_by_user_id),
        )
        self._repository.add_manual_review_action(action)
        self._repository.flush()
        self._audit_service.record_manual_review_action(
            case_id=case_id,
            action_id=action.id,
            performed_by_user_id=performed_by_user_id,
            action_type=action_type,
            document_id=document_id,
            comment=comment,
            payload=payload,
            evidence_refs=list(evidence_refs),
            occurred_at=occurred_at,
        )
        return action

    def _set_review_status(self, *, document: Document | None, occurred_at: datetime, actor_id: str) -> None:
        if document is not None:
            document.status = DocumentStatus.REVIEW_REQUIRED
            document.status_changed_at = occurred_at
            document.updated_at = occurred_at
            document.updated_by = actor_id

    def _clear_review_status(self, *, document: Document | None, occurred_at: datetime, actor_id: str) -> None:
        if document is not None and document.status == DocumentStatus.REVIEW_REQUIRED:
            document.status = DocumentStatus.EXTRACTION_COMPLETED
            document.status_changed_at = occurred_at
            document.updated_at = occurred_at
            document.updated_by = actor_id

    def _to_workflow_response(
        self,
        *,
        case_id: UUID,
        case_status: CaseStatus,
        status_changed_at: datetime,
        action: ManualReviewAction,
    ) -> ManualReviewWorkflowResponse:
        return ManualReviewWorkflowResponse(
            case_id=case_id,
            case_status=case_status,
            status_changed_at=status_changed_at,
            allowed_next_statuses=list(self._workflow_service.allowed_targets(case_status)),
            action=self._to_action_response(action),
        )

    @staticmethod
    def _to_action_response(action: ManualReviewAction) -> ManualReviewActionResponse:
        return ManualReviewActionResponse(
            id=action.id,
            case_id=action.case_id,
            document_id=action.document_id,
            performed_by_user_id=action.performed_by_user_id,
            related_decision_id=action.related_decision_id,
            action_type=action.action_type,
            comment=action.comment,
            payload=action.payload,
            evidence_refs=[EvidenceReferenceResponse.model_validate(ref) for ref in action.evidence_refs],
            created_at=action.created_at,
            updated_at=action.updated_at,
        )

    @staticmethod
    def _default_reason_code_for_target(target_status: CaseStatus) -> str:
        return "manual_reprocessing_requested" if target_status == CaseStatus.QUEUED_FOR_PROCESSING else "manual_review_completed"

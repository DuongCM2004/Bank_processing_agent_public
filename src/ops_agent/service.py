from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from fastapi import HTTPException, status

from ops_agent.application.services.document_application_service import DocumentApplicationService
from ops_agent.application.services.processing_application_service import ProcessingApplicationService
from ops_agent.application.services.result_persistence_service import ResultPersistenceService
from ops_agent.models import (
    AuditActorType,
    AuditEvent,
    CaseCreateRequest,
    CaseCreateResponse,
    CaseRecord,
    CaseResults,
    CaseStatus,
    CaseStatusView,
    CloseCaseRequest,
    DecisionRecord,
    DocumentCreate,
    DocumentRecord,
    EscalationRequest,
    FieldCorrectionRequest,
    FieldResult,
    ProcessingAcceptedResponse,
    ProcessingTriggerRequest,
    Priority,
    ProcessingStatus,
    ReviewActionRecord,
    ReviewActionType,
    ReviewTaskClaimRequest,
    ReviewTaskListResponse,
    ReviewTaskRecord,
    ReviewTaskStatus,
    RevalidateRequest,
    new_id,
    utc_now,
)
from ops_agent.repository import InMemoryRepository
from ops_agent.state_machine import CaseStateMachine, InvalidStateTransitionError


ALLOWED_CLOSE_OUTCOMES = {"approved", "rejected", "closed_without_decision"}


class CaseWorkflowService:
    def __init__(self, repository: InMemoryRepository) -> None:
        self.repository = repository
        self.state_machine = CaseStateMachine.default()
        self.document_service = DocumentApplicationService(repository)
        self.processing_service = ProcessingApplicationService(repository)
        self.result_persistence_service = ResultPersistenceService(repository)

    def create_case(self, request: CaseCreateRequest) -> CaseCreateResponse:
        now = utc_now()
        case = CaseRecord(
            case_id=new_id("case"),
            workflow_type=request.workflow_type,
            priority=request.priority,
            customer_reference=request.customer_reference,
            status=CaseStatus.RECEIVED,
            review_required=request.review_required,
            assigned_queue=self._queue_for_priority(request.priority, request.review_required),
            created_at=now,
            updated_at=now,
        )
        self.repository.save_case(case)
        self._audit(case.case_id, "case", case.case_id, "case_created", AuditActorType.USER, "system_bootstrap")

        documents = [self._create_document(case.case_id, document, now) for document in request.documents]
        case.document_ids = [document.document_id for document in documents]
        case = self._transition(case, CaseStatus.STORED, "documents_stored", actor_id="system")
        case = self._transition(case, CaseStatus.QUEUED, "case_queued", actor_id="system")

        self.result_persistence_service.initialize_case_results(case_id=case.case_id, review_required=request.review_required)
        self._audit(case.case_id, "case_results", case.case_id, "results_initialized", AuditActorType.SYSTEM, "workflow_orchestrator")

        review_tasks: list[ReviewTaskRecord] = []
        if request.review_required:
            review_task = self._create_review_task(
                case,
                assigned_queue=case.assigned_queue,
                reason_codes=["mvp_default_review_gate"],
                created_at=now,
            )
            review_tasks.append(review_task)
            case.review_task_ids = [review_task.task_id]
            case = self._transition(case, CaseStatus.REVIEW_REQUIRED, "review_task_created", actor_id="system")

        self.repository.save_case(case)
        return CaseCreateResponse(case=case, documents=documents, review_tasks=review_tasks)

    def get_case(self, case_id: str) -> CaseRecord:
        case = self.repository.get_case(case_id)
        if not case:
            raise self._not_found("case_not_found", f"Case {case_id} was not found.")
        return case

    def add_document(self, case_id: str, document: DocumentCreate) -> DocumentRecord:
        case = self.get_case(case_id)
        if case.status == CaseStatus.CLOSED:
            raise self._conflict("case_closed", f"Case {case_id} is closed and cannot accept new documents.")

        record = self._create_document(case_id, document, utc_now())
        case.document_ids.append(record.document_id)
        case.updated_at = utc_now()
        self.repository.save_case(case)
        self._audit(case_id, "case", case_id, "document_attached_to_case", AuditActorType.USER, "system")
        return record

    def get_document(self, case_id: str, document_id: str) -> DocumentRecord:
        case = self.get_case(case_id)
        if document_id not in case.document_ids:
            raise self._not_found("document_not_found", f"Document {document_id} does not belong to case {case_id}.")
        document = self.repository.get_document(document_id)
        if not document:
            raise self._not_found("document_not_found", f"Document {document_id} was not found.")
        return document

    def get_results(self, case_id: str) -> CaseResults:
        self.get_case(case_id)
        results = self.repository.get_results(case_id)
        if not results:
            raise self._not_found("results_not_found", f"Results for case {case_id} were not found.")
        return results

    def get_case_status(self, case_id: str) -> CaseStatusView:
        case = self.get_case(case_id)
        return self.processing_service.get_case_status(case)

    def start_processing(self, case_id: str, request: ProcessingTriggerRequest) -> ProcessingAcceptedResponse:
        case = self.get_case(case_id)
        accepted = self.processing_service.start_processing(case, request)
        self.result_persistence_service.mark_processing_started(case_id=case_id)
        return accepted

    def list_review_tasks(self, status_filter: str | None = None) -> ReviewTaskListResponse:
        return ReviewTaskListResponse(items=self.repository.list_review_tasks(status=status_filter))

    def claim_review_task(self, task_id: str, request: ReviewTaskClaimRequest) -> ReviewTaskRecord:
        task = self.repository.get_review_task(task_id)
        if not task:
            raise self._not_found("review_task_not_found", f"Review task {task_id} was not found.")
        if task.status not in {ReviewTaskStatus.OPEN, ReviewTaskStatus.CLAIMED}:
            raise self._conflict("invalid_task_state", f"Review task {task_id} is not claimable.")

        task.status = ReviewTaskStatus.CLAIMED
        task.assigned_to = request.reviewer_id
        task.updated_at = utc_now()
        self.repository.save_review_task(task)

        case = self.get_case(task.case_id)
        if case.status == CaseStatus.REVIEW_REQUIRED:
            self._transition(case, CaseStatus.IN_REVIEW, "review_started", actor_id=request.reviewer_id)

        action = ReviewActionRecord(
            action_id=new_id("review_action"),
            case_id=task.case_id,
            task_id=task.task_id,
            action_type=ReviewActionType.CLAIM,
            actor_id=request.reviewer_id,
            reason_code="task_claimed",
            created_at=utc_now(),
        )
        self.repository.save_review_action(action)
        self._audit(task.case_id, "review_task", task.task_id, "review_task_claimed", AuditActorType.USER, request.reviewer_id)
        return task

    def submit_field_corrections(self, case_id: str, request: FieldCorrectionRequest) -> CaseRecord:
        case = self.get_case(case_id)
        results = self.get_results(case_id)
        now = utc_now()

        for correction in request.corrections:
            results.fields.append(
                FieldResult(
                    field_name=correction.field_name,
                    value=correction.new_value,
                    normalized_value=correction.new_value,
                    confidence=1.0,
                    required=True,
                    evidence_refs=correction.evidence_refs,
                    reason_code=correction.reason_code,
                )
            )

        self.repository.save_results(results)
        payload = {"corrections": [item.model_dump(mode="json") for item in request.corrections]}
        action = ReviewActionRecord(
            action_id=new_id("review_action"),
            case_id=case_id,
            action_type=ReviewActionType.CORRECT_FIELD,
            actor_id=request.reviewer_id,
            reason_code="field_corrections_submitted",
            comment=request.comment,
            payload=payload,
            created_at=now,
        )
        self.repository.save_review_action(action)
        updated_case = self._transition(case, CaseStatus.CORRECTED, "field_corrections_recorded", actor_id=request.reviewer_id)
        self._audit(case_id, "case", case_id, "field_corrections_submitted", AuditActorType.USER, request.reviewer_id, details=payload)
        return updated_case

    def escalate_case(self, case_id: str, request: EscalationRequest) -> CaseRecord:
        case = self.get_case(case_id)
        payload = {
            "escalation_target": request.escalation_target,
            "reason_code": request.reason_code,
            "comment": request.comment,
        }
        action = ReviewActionRecord(
            action_id=new_id("review_action"),
            case_id=case_id,
            action_type=ReviewActionType.ESCALATE,
            actor_id=request.reviewer_id,
            reason_code=request.reason_code,
            comment=request.comment,
            payload=payload,
            created_at=utc_now(),
        )
        self.repository.save_review_action(action)
        updated_case = self._transition(case, CaseStatus.ESCALATED, "case_escalated", actor_id=request.reviewer_id)
        self._audit(case_id, "case", case_id, "case_escalated", AuditActorType.USER, request.reviewer_id, details=payload)
        return updated_case

    def revalidate_case(self, case_id: str, request: RevalidateRequest) -> CaseRecord:
        case = self.get_case(case_id)
        results = self.get_results(case_id)
        results.validation_status = ProcessingStatus.IN_PROGRESS
        self.repository.save_results(results)

        action = ReviewActionRecord(
            action_id=new_id("review_action"),
            case_id=case_id,
            action_type=ReviewActionType.REVALIDATE,
            actor_id=request.requested_by,
            reason_code=request.reason_code,
            created_at=utc_now(),
        )
        self.repository.save_review_action(action)

        updated_case = self._transition(case, CaseStatus.VALIDATED, "manual_revalidation_triggered", actor_id=request.requested_by)
        results.validation_status = ProcessingStatus.COMPLETE
        self.repository.save_results(results)
        self._audit(case_id, "case", case_id, "case_revalidated", AuditActorType.USER, request.requested_by, details={"reason_code": request.reason_code})
        return updated_case

    def close_case(self, case_id: str, request: CloseCaseRequest) -> CaseRecord:
        if request.outcome not in ALLOWED_CLOSE_OUTCOMES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "invalid_close_outcome",
                    "message": f"Outcome must be one of {sorted(ALLOWED_CLOSE_OUTCOMES)}.",
                },
            )
        case = self.get_case(case_id)
        if request.outcome == "approved":
            case = self._transition(case, CaseStatus.APPROVED, "case_approved", actor_id=request.requested_by)
        elif request.outcome == "rejected":
            case = self._transition(case, CaseStatus.REJECTED, "case_rejected", actor_id=request.requested_by)
        case.final_outcome = request.outcome
        case = self._transition(case, CaseStatus.CLOSED, "case_closed", actor_id=request.requested_by)
        self.result_persistence_service.record_decision(
            case_id=case_id,
            workflow_run_id=self._active_workflow_run_id(case_id),
            decision_type="manual_final_decision",
            outcome=request.outcome,
            actor_id=request.requested_by,
            actor_type=AuditActorType.USER,
            reason_code=request.reason_code,
            created_at=utc_now(),
        )
        self._audit(case_id, "case", case_id, "case_closed", AuditActorType.USER, request.requested_by, details={"outcome": request.outcome, "reason_code": request.reason_code})
        return case

    def get_latest_decision(self, case_id: str) -> DecisionRecord:
        self.get_case(case_id)
        decision = self.repository.get_latest_decision(case_id)
        if not decision:
            raise self._not_found("decision_not_found", f"No decision was found for case {case_id}.")
        return decision

    def list_audit_events(self, case_id: str) -> Iterable[AuditEvent]:
        self.get_case(case_id)
        return self.repository.list_audit_events(case_id)

    def _create_document(self, case_id: str, document: DocumentCreate, now) -> DocumentRecord:
        record = self.document_service.create_document(case_id=case_id, request=document, created_at=now)
        self._audit(case_id, "document", record.document_id, "document_registered", AuditActorType.SYSTEM, "ingestion_service")
        return record

    def _create_review_task(
        self,
        case: CaseRecord,
        *,
        assigned_queue: str,
        reason_codes: list[str],
        created_at: datetime,
    ) -> ReviewTaskRecord:
        task = ReviewTaskRecord(
            task_id=new_id("review_task"),
            case_id=case.case_id,
            status=ReviewTaskStatus.OPEN,
            assigned_queue=assigned_queue,
            reason_codes=reason_codes,
            created_at=created_at,
            updated_at=created_at,
        )
        self.repository.save_review_task(task)
        self._audit(case.case_id, "review_task", task.task_id, "review_task_created", AuditActorType.SYSTEM, "workflow_orchestrator", details={"reason_codes": reason_codes})
        return task

    def _transition(self, case: CaseRecord, new_status: CaseStatus, reason_code: str, *, actor_id: str) -> CaseRecord:
        try:
            self.state_machine.assert_transition(case_id=case.case_id, from_status=case.status, to_status=new_status)
        except InvalidStateTransitionError as exc:
            raise self._conflict("invalid_state_transition", str(exc)) from exc
        case.status = new_status
        case.updated_at = utc_now()
        self.repository.save_case(case)
        actor_type = AuditActorType.USER if actor_id != "system" else AuditActorType.SYSTEM
        self._audit(case.case_id, "case", case.case_id, "case_state_changed", actor_type, actor_id, details={"new_status": new_status, "reason_code": reason_code})
        return case

    def _queue_for_priority(self, priority: Priority, review_required: bool) -> str:
        if review_required and priority in {Priority.HIGH, Priority.CRITICAL}:
            return "priority_review"
        if review_required:
            return "ops_review"
        return "processing"

    def _active_workflow_run_id(self, case_id: str) -> str | None:
        workflow_run = self.repository.get_latest_workflow_run(case_id)
        if not workflow_run:
            return None
        return workflow_run.workflow_run_id

    def _audit(
        self,
        case_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        actor_type: AuditActorType,
        actor_id: str,
        *,
        details: dict | None = None,
    ) -> None:
        event = AuditEvent(
            event_id=new_id("audit"),
            case_id=case_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            actor_type=actor_type,
            actor_id=actor_id,
            occurred_at=utc_now(),
            details=details or {},
        )
        self.repository.save_audit_event(event)

    def _not_found(self, error_code: str, message: str) -> HTTPException:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error_code": error_code, "message": message})

    def _conflict(self, error_code: str, message: str) -> HTTPException:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error_code": error_code, "message": message})

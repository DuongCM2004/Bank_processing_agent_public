from __future__ import annotations

from fastapi import HTTPException, status

from ops_agent.models import (
    AuditActorType,
    AuditEvent,
    CaseRecord,
    CaseStatus,
    CaseStatusView,
    ProcessingAcceptedResponse,
    ProcessingStatus,
    ProcessingTriggerRequest,
    WorkflowRunRecord,
    WorkflowRunStatus,
    WorkflowStepRunRecord,
    WorkflowStepStatus,
    new_id,
    utc_now,
)
from ops_agent.repository import InMemoryRepository
from ops_agent.state_machine import CaseStateMachine, InvalidStateTransitionError
from ops_agent.workflow_contracts import ReviewCompletionSignal, WorkflowRunStatusResponse, WorkflowStartCommand


class ProcessingApplicationService:
    def __init__(self, repository: InMemoryRepository) -> None:
        self.repository = repository
        self.state_machine = CaseStateMachine.default()

    def start_processing(self, case: CaseRecord, request: ProcessingTriggerRequest) -> ProcessingAcceptedResponse:
        existing = self.repository.get_active_workflow_run(case.case_id)
        if existing:
            return ProcessingAcceptedResponse(
                case_id=case.case_id,
                workflow_run_id=existing.workflow_run_id,
                workflow_status=existing.status,
                case_status=case.status,
                accepted_at=utc_now(),
            )
        if case.status != CaseStatus.QUEUED:
            raise self._conflict("case_not_processable", f"Case {case.case_id} must be queued before processing starts.")

        started_at = utc_now()
        self._assert_transition(case=case, new_status=CaseStatus.PROCESSING)
        case.status = CaseStatus.PROCESSING
        case.updated_at = started_at
        self.repository.save_case(case)

        workflow_run = WorkflowRunRecord(
            workflow_run_id=new_id("wf"),
            case_id=case.case_id,
            workflow_type=case.workflow_type,
            status=WorkflowRunStatus.IN_PROGRESS,
            active_step="ingestion",
            started_by=request.requested_by,
            started_at=started_at,
            updated_at=started_at,
        )
        self.repository.save_workflow_run(workflow_run)
        self.repository.save_workflow_step_run(
            WorkflowStepRunRecord(
                step_run_id=new_id("wf_step"),
                workflow_run_id=workflow_run.workflow_run_id,
                case_id=case.case_id,
                step_name="ingestion",
                status=WorkflowStepStatus.IN_PROGRESS,
                started_at=started_at,
                updated_at=started_at,
            )
        )
        self._audit(
            case_id=case.case_id,
            resource_type="workflow_run",
            resource_id=workflow_run.workflow_run_id,
            action="processing_started",
            actor_type=AuditActorType.USER,
            actor_id=request.requested_by,
            details={"reason_code": request.reason_code},
        )
        return ProcessingAcceptedResponse(
            case_id=case.case_id,
            workflow_run_id=workflow_run.workflow_run_id,
            workflow_status=workflow_run.status,
            case_status=case.status,
            accepted_at=started_at,
        )

    def start_from_command(self, command: WorkflowStartCommand) -> ProcessingAcceptedResponse:
        case = self.repository.get_case(command.case_id)
        if not case:
            raise self._not_found("case_not_found", f"Case {command.case_id} was not found.")
        return self.start_processing(
            case,
            ProcessingTriggerRequest(
                requested_by=command.initiated_by,
                reason_code="workflow_start_command",
            ),
        )

    def get_case_status(self, case: CaseRecord) -> CaseStatusView:
        results = self.repository.get_results(case.case_id)
        workflow_run = self.repository.get_latest_workflow_run(case.case_id)
        latest_decision = self.repository.get_latest_decision(case.case_id)
        return CaseStatusView(
            case_id=case.case_id,
            case_status=case.status,
            extraction_status=results.extraction_status if results else ProcessingStatus.NOT_STARTED,
            validation_status=results.validation_status if results else ProcessingStatus.NOT_STARTED,
            workflow_run_id=workflow_run.workflow_run_id if workflow_run else None,
            workflow_status=workflow_run.status if workflow_run else None,
            active_step=workflow_run.active_step if workflow_run else None,
            pending_review_task_id=workflow_run.pending_review_task_id if workflow_run else None,
            latest_decision_outcome=latest_decision.outcome if latest_decision else None,
            updated_at=case.updated_at,
        )

    def get_workflow_status(self, case_id: str) -> WorkflowRunStatusResponse:
        workflow_run = self.repository.get_latest_workflow_run(case_id)
        if not workflow_run:
            raise self._not_found("workflow_not_found", f"No workflow run was found for case {case_id}.")
        return WorkflowRunStatusResponse(
            workflow_run_id=workflow_run.workflow_run_id,
            case_id=case_id,
            status=workflow_run.status,
            active_step=workflow_run.active_step,
            pending_review_task_id=workflow_run.pending_review_task_id,
            started_at_utc=workflow_run.started_at,
            updated_at_utc=workflow_run.updated_at,
            retryable_failure_count=workflow_run.retryable_failure_count,
            latest_error_code=workflow_run.latest_error_code,
        )

    def signal_review_complete(self, *, case_id: str, request: ReviewCompletionSignal) -> dict[str, str]:
        workflow_run = self.repository.get_active_workflow_run(case_id)
        if not workflow_run:
            raise self._not_found("workflow_not_found", f"No active workflow run was found for case {case_id}.")
        workflow_run.status = WorkflowRunStatus.IN_PROGRESS
        workflow_run.active_step = "review_completion"
        workflow_run.pending_review_task_id = None
        workflow_run.updated_at = utc_now()
        self.repository.save_workflow_run(workflow_run)
        self._audit(
            case_id=case_id,
            resource_type="workflow_run",
            resource_id=workflow_run.workflow_run_id,
            action="review_completion_signal_received",
            actor_type=AuditActorType.USER,
            actor_id=request.triggered_by,
            details={"review_task_id": request.review_task_id, "outcome": request.outcome},
        )
        return {"status": "accepted", "case_id": case_id, "review_task_id": request.review_task_id}

    def _assert_transition(self, *, case: CaseRecord, new_status: CaseStatus) -> None:
        try:
            self.state_machine.assert_transition(case_id=case.case_id, from_status=case.status, to_status=new_status)
        except InvalidStateTransitionError as exc:
            raise self._conflict("invalid_state_transition", str(exc)) from exc

    def _audit(
        self,
        *,
        case_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        actor_type: AuditActorType,
        actor_id: str,
        details: dict | None = None,
    ) -> None:
        self.repository.save_audit_event(
            AuditEvent(
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
        )

    def _not_found(self, error_code: str, message: str) -> HTTPException:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error_code": error_code, "message": message})

    def _conflict(self, error_code: str, message: str) -> HTTPException:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error_code": error_code, "message": message})

from __future__ import annotations

from collections.abc import Iterable

from ops_agent.models import (
    AuditEvent,
    CaseCreateRequest,
    CaseCreateResponse,
    CaseRecord,
    CaseResults,
    CaseStatusView,
    CloseCaseRequest,
    DecisionRecord,
    DocumentCreate,
    DocumentRecord,
    EscalationRequest,
    FieldCorrectionRequest,
    ProcessingAcceptedResponse,
    ProcessingTriggerRequest,
    ReviewTaskClaimRequest,
    ReviewTaskListResponse,
    ReviewTaskRecord,
    RevalidateRequest,
)
from ops_agent.service import CaseWorkflowService


class CaseApplicationService:
    """Thin application facade around the current workflow service.

    This isolates the API layer from the legacy service implementation and gives
    the team a stable place to split commands and queries later.
    """

    def __init__(self, workflow_service: CaseWorkflowService) -> None:
        self.workflow_service = workflow_service

    def create_case(self, request: CaseCreateRequest) -> CaseCreateResponse:
        return self.workflow_service.create_case(request)

    def get_case(self, case_id: str) -> CaseRecord:
        return self.workflow_service.get_case(case_id)

    def add_document(self, case_id: str, request: DocumentCreate) -> DocumentRecord:
        return self.workflow_service.add_document(case_id, request)

    def get_document(self, case_id: str, document_id: str) -> DocumentRecord:
        return self.workflow_service.get_document(case_id, document_id)

    def get_results(self, case_id: str) -> CaseResults:
        return self.workflow_service.get_results(case_id)

    def list_review_tasks(self, status_filter: str | None = None) -> ReviewTaskListResponse:
        return self.workflow_service.list_review_tasks(status_filter=status_filter)

    def claim_review_task(self, task_id: str, request: ReviewTaskClaimRequest) -> ReviewTaskRecord:
        return self.workflow_service.claim_review_task(task_id, request)

    def submit_field_corrections(self, case_id: str, request: FieldCorrectionRequest) -> CaseRecord:
        return self.workflow_service.submit_field_corrections(case_id, request)

    def escalate_case(self, case_id: str, request: EscalationRequest) -> CaseRecord:
        return self.workflow_service.escalate_case(case_id, request)

    def revalidate_case(self, case_id: str, request: RevalidateRequest) -> CaseRecord:
        return self.workflow_service.revalidate_case(case_id, request)

    def close_case(self, case_id: str, request: CloseCaseRequest) -> CaseRecord:
        return self.workflow_service.close_case(case_id, request)

    def start_processing(self, case_id: str, request: ProcessingTriggerRequest) -> ProcessingAcceptedResponse:
        return self.workflow_service.start_processing(case_id, request)

    def get_case_status(self, case_id: str) -> CaseStatusView:
        return self.workflow_service.get_case_status(case_id)

    def get_latest_decision(self, case_id: str) -> DecisionRecord:
        return self.workflow_service.get_latest_decision(case_id)

    def list_audit_events(self, case_id: str) -> Iterable[AuditEvent]:
        return self.workflow_service.list_audit_events(case_id)

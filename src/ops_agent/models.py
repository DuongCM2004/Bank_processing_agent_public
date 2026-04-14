from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class Priority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class CaseStatus(StrEnum):
    RECEIVED = "received"
    STORED = "stored"
    QUEUED = "queued"
    PROCESSING = "processing"
    VALIDATED = "validated"
    REVIEW_REQUIRED = "review_required"
    IN_REVIEW = "in_review"
    CORRECTED = "corrected"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    FAILED = "failed"
    CLOSED = "closed"


class ReviewTaskStatus(StrEnum):
    OPEN = "open"
    CLAIMED = "claimed"
    COMPLETED = "completed"


class ReviewActionType(StrEnum):
    CLAIM = "claim"
    CORRECT_FIELD = "correct_field"
    ESCALATE = "escalate"
    REVALIDATE = "revalidate"
    CLOSE = "close"


class AuditActorType(StrEnum):
    SYSTEM = "system"
    USER = "user"


class ProcessingStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


class WorkflowRunStatus(StrEnum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    WAITING_REVIEW = "waiting_review"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStepStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class APIModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True)


class EvidenceRef(APIModel):
    document_id: str
    page_number: int | None = None
    text_span: str | None = None
    bounding_box: dict[str, float] | None = None


class DocumentCreate(APIModel):
    filename: str
    mime_type: str
    source_channel: str = Field(default="manual_upload")
    retention_class: str = Field(default="bank_ops_default")


class CaseCreateRequest(APIModel):
    workflow_type: str
    priority: Priority = Priority.NORMAL
    customer_reference: str | None = None
    review_required: bool = True
    documents: list[DocumentCreate] = Field(default_factory=list)


class DocumentRecord(APIModel):
    document_id: str
    case_id: str
    filename: str
    mime_type: str
    source_channel: str
    retention_class: str
    file_hash: str
    status: ProcessingStatus
    created_at: datetime


class DocumentVersionRecord(APIModel):
    document_version_id: str
    document_id: str
    case_id: str
    version_number: int
    file_hash: str
    storage_status: str
    created_at: datetime


class WorkflowStepRunRecord(APIModel):
    step_run_id: str
    workflow_run_id: str
    case_id: str
    step_name: str
    status: WorkflowStepStatus
    attempt_no: int = 1
    started_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    error_code: str | None = None


class WorkflowRunRecord(APIModel):
    workflow_run_id: str
    case_id: str
    workflow_type: str
    status: WorkflowRunStatus
    active_step: str | None = None
    pending_review_task_id: str | None = None
    started_by: str
    started_at: datetime
    updated_at: datetime
    latest_error_code: str | None = None
    retryable_failure_count: int = 0


class ReviewTaskRecord(APIModel):
    task_id: str
    case_id: str
    status: ReviewTaskStatus
    assigned_to: str | None = None
    assigned_queue: str
    reason_codes: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CaseRecord(APIModel):
    case_id: str
    workflow_type: str
    priority: Priority
    customer_reference: str | None = None
    status: CaseStatus
    review_required: bool
    assigned_queue: str
    created_at: datetime
    updated_at: datetime
    document_ids: list[str] = Field(default_factory=list)
    review_task_ids: list[str] = Field(default_factory=list)
    final_outcome: str | None = None


class CaseCreateResponse(APIModel):
    case: CaseRecord
    documents: list[DocumentRecord]
    review_tasks: list[ReviewTaskRecord]


class FieldResult(APIModel):
    field_name: str
    value: str | None = None
    normalized_value: str | None = None
    confidence: float | None = None
    required: bool = True
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    reason_code: str | None = None


class ValidationResult(APIModel):
    rule_id: str
    rule_version: str
    result: str
    severity: str
    reason_code: str
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


class ExtractionRunRecord(APIModel):
    extraction_run_id: str
    case_id: str
    workflow_run_id: str
    document_id: str
    schema_name: str
    status: ProcessingStatus
    field_count: int
    confidence: float | None = None
    recommended_route: str = "review_required"
    created_at: datetime


class ValidationRunRecord(APIModel):
    validation_run_id: str
    case_id: str
    workflow_run_id: str
    status: ProcessingStatus
    finding_count: int
    recommended_route: str = "review_required"
    created_at: datetime


class DecisionRecord(APIModel):
    decision_id: str
    case_id: str
    workflow_run_id: str | None = None
    decision_type: str
    outcome: str
    actor_id: str
    actor_type: str
    reason_code: str
    confidence: float | None = None
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    created_at: datetime


class CaseResults(APIModel):
    case_id: str
    extraction_status: ProcessingStatus
    validation_status: ProcessingStatus
    fields: list[FieldResult] = Field(default_factory=list)
    validations: list[ValidationResult] = Field(default_factory=list)
    recommended_route: str = "review_required"


class ProcessingTriggerRequest(APIModel):
    requested_by: str
    reason_code: str = "manual_processing_trigger"


class ProcessingAcceptedResponse(APIModel):
    case_id: str
    workflow_run_id: str
    workflow_status: WorkflowRunStatus
    case_status: CaseStatus
    accepted_at: datetime


class CaseStatusView(APIModel):
    case_id: str
    case_status: CaseStatus
    extraction_status: ProcessingStatus
    validation_status: ProcessingStatus
    workflow_run_id: str | None = None
    workflow_status: WorkflowRunStatus | None = None
    active_step: str | None = None
    pending_review_task_id: str | None = None
    latest_decision_outcome: str | None = None
    updated_at: datetime


class ReviewTaskListResponse(APIModel):
    items: list[ReviewTaskRecord]


class ReviewTaskClaimRequest(APIModel):
    reviewer_id: str


class FieldCorrection(APIModel):
    field_name: str
    new_value: str | None = None
    reason_code: str
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


class FieldCorrectionRequest(APIModel):
    reviewer_id: str
    comment: str | None = None
    corrections: list[FieldCorrection]


class EscalationRequest(APIModel):
    reviewer_id: str
    escalation_target: str
    reason_code: str
    comment: str | None = None


class RevalidateRequest(APIModel):
    requested_by: str
    reason_code: str


class CloseCaseRequest(APIModel):
    requested_by: str
    outcome: str
    reason_code: str


class ReviewActionRecord(APIModel):
    action_id: str
    case_id: str
    task_id: str | None = None
    action_type: ReviewActionType
    actor_id: str
    reason_code: str
    comment: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AuditEvent(APIModel):
    event_id: str
    case_id: str
    resource_type: str
    resource_id: str
    action: str
    actor_type: AuditActorType
    actor_id: str
    occurred_at: datetime
    details: dict[str, Any] = Field(default_factory=dict)


class AuditEventListResponse(APIModel):
    items: list[AuditEvent]


class ErrorResponse(APIModel):
    error_code: str
    message: str
    trace_id: str
    retryable: bool = False
    details: dict[str, Any] | None = None

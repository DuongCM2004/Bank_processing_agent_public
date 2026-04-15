from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ops_agent.domain.shared.enums import (
    AuditActorType,
    AuditEventType,
    CaseStatus,
    DecisionOutcome,
    DecisionType,
    DocumentStatus,
    FindingSeverity,
    FindingStatus,
    ManualReviewActionType,
    ProcessingStatus,
    RiskLevel,
    RoleCode,
    UserStatus,
)


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class HealthcheckResponse(APIModel):
    status: str
    service: str
    checks: dict[str, str]


class BoundingBoxResponse(APIModel):
    x: float = Field(..., ge=0)
    y: float = Field(..., ge=0)
    width: float = Field(..., ge=0)
    height: float = Field(..., ge=0)


class EvidenceReferenceResponse(APIModel):
    document_id: UUID
    page_number: int | None = Field(default=None, ge=1)
    text_anchor: str | None = None
    bounding_box: BoundingBoxResponse | None = None
    extracted_value: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class EvidenceReferenceRequest(APIModel):
    document_id: UUID
    page_number: int | None = Field(default=None, ge=1)
    text_anchor: str | None = None
    bounding_box: BoundingBoxResponse | None = None
    extracted_value: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class RoleResponse(APIModel):
    id: UUID
    code: RoleCode
    name: str
    description: str | None = None


class UserSummaryResponse(APIModel):
    id: UUID
    username: str
    email: str
    display_name: str
    status: UserStatus
    roles: list[RoleResponse] = Field(default_factory=list)


class DocumentUploadMetadataRequest(APIModel):
    filename: str = Field(..., min_length=1, max_length=255)
    document_type: str = Field(..., min_length=1, max_length=80)
    mime_type: str = Field(..., min_length=1, max_length=120)
    source_channel: str = Field(default="manual_upload", min_length=1, max_length=80)
    sha256_digest: str = Field(..., min_length=32, max_length=128)
    storage_key: str = Field(..., min_length=1, max_length=255)
    file_size_bytes: int | None = Field(default=None, ge=0)
    page_count: int | None = Field(default=None, ge=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class DocumentUploadMetadataResponse(APIModel):
    id: UUID
    case_id: UUID
    filename: str
    document_type: str
    mime_type: str
    source_channel: str
    storage_key: str
    sha256_digest: str
    file_size_bytes: int | None = Field(default=None, ge=0)
    uploaded_at: datetime
    status: DocumentStatus
    status_changed_at: datetime
    page_count: int | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class DocumentUploadRequest(APIModel):
    document_type: str = Field(..., min_length=1, max_length=80)
    source_channel: str = Field(default="manual_upload", min_length=1, max_length=80)
    uploaded_by_user_id: UUID | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class DocumentListResponse(APIModel):
    items: list[DocumentUploadMetadataResponse] = Field(default_factory=list)
    total: int


class CaseCreateRequest(APIModel):
    case_type: str = Field(..., min_length=1, max_length=80)
    source_channel: str = Field(default="manual_upload", min_length=1, max_length=80)
    customer_reference: str | None = Field(default=None, max_length=120)
    current_queue: str = Field(default="document_ops", min_length=1, max_length=80)
    submitted_by_user_id: UUID | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    documents: list[DocumentUploadMetadataRequest] = Field(default_factory=list)


class CaseCreateResponse(APIModel):
    id: UUID
    case_reference: str
    case_type: str
    status: CaseStatus
    status_changed_at: datetime
    current_queue: str
    source_channel: str
    customer_reference: str | None = None
    submitted_by_user_id: UUID | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    documents: list[DocumentUploadMetadataResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CaseSummaryResponse(APIModel):
    id: UUID
    case_reference: str
    case_type: str
    status: CaseStatus
    status_changed_at: datetime
    current_queue: str
    source_channel: str
    customer_reference: str | None = None
    document_count: int = 0
    created_at: datetime
    updated_at: datetime


class OCRResultResponse(APIModel):
    id: UUID
    document_id: UUID
    status: ProcessingStatus
    raw_text: str | None = None
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    provider_name: str
    provider_job_id: str | None = None
    processed_at: datetime | None = None
    page_count: int | None = None
    result_metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ExtractionResultResponse(APIModel):
    id: UUID
    document_id: UUID
    ocr_result_id: UUID | None = None
    status: ProcessingStatus
    schema_name: str
    extracted_payload: dict[str, object] = Field(default_factory=dict)
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    evidence_refs: list[EvidenceReferenceResponse] = Field(default_factory=list)
    provider_name: str
    provider_job_id: str | None = None
    processed_at: datetime | None = None
    model_version: str | None = None
    created_at: datetime
    updated_at: datetime


class ValidationFindingResponse(APIModel):
    id: UUID
    case_id: UUID
    document_id: UUID | None = None
    extraction_result_id: UUID | None = None
    rule_code: str
    field_name: str | None = None
    message: str
    severity: FindingSeverity
    status: FindingStatus
    resolution_note: str | None = None
    evidence_refs: list[EvidenceReferenceResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class RiskFindingResponse(APIModel):
    id: UUID
    case_id: UUID
    document_id: UUID | None = None
    extraction_result_id: UUID | None = None
    risk_code: str
    message: str
    risk_level: RiskLevel
    status: FindingStatus
    risk_score: float | None = None
    evidence_refs: list[EvidenceReferenceResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ComplianceFindingResponse(APIModel):
    id: UUID
    case_id: UUID
    document_id: UUID | None = None
    extraction_result_id: UUID | None = None
    policy_code: str
    regulation_reference: str | None = None
    message: str
    severity: FindingSeverity
    status: FindingStatus
    evidence_refs: list[EvidenceReferenceResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ValidationResultResponse(APIModel):
    case_id: UUID
    validation_findings: list[ValidationFindingResponse] = Field(default_factory=list)
    risk_findings: list[RiskFindingResponse] = Field(default_factory=list)
    compliance_findings: list[ComplianceFindingResponse] = Field(default_factory=list)
    has_blocking_findings: bool


class DecisionResponse(APIModel):
    id: UUID
    case_id: UUID
    decided_by_user_id: UUID | None = None
    decision_type: DecisionType
    outcome: DecisionOutcome
    reason_code: str
    rationale: str | None = None
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    evidence_refs: list[EvidenceReferenceResponse] = Field(default_factory=list)
    linked_findings: list["DecisionFindingLinkResponse"] = Field(default_factory=list)
    supersedes_decision_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class DecisionFindingLinkRequest(APIModel):
    finding_type: str = Field(..., min_length=1, max_length=40)
    finding_id: UUID


class DecisionFindingLinkResponse(APIModel):
    finding_type: str
    finding_id: UUID


class DecisionCreateRequest(APIModel):
    decided_by_user_id: UUID
    decision_type: DecisionType = DecisionType.REVIEWER_DECISION
    outcome: DecisionOutcome
    reason_code: str = Field(..., min_length=1, max_length=100)
    rationale: str | None = Field(default=None, max_length=4000)
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    evidence_refs: list[EvidenceReferenceRequest] = Field(default_factory=list)
    linked_findings: list[DecisionFindingLinkRequest] = Field(default_factory=list)
    supersedes_decision_id: UUID | None = None


class DecisionActionRequest(APIModel):
    decided_by_user_id: UUID
    decision_type: DecisionType = DecisionType.REVIEWER_DECISION
    reason_code: str = Field(..., min_length=1, max_length=100)
    rationale: str | None = Field(default=None, max_length=4000)
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    evidence_refs: list[EvidenceReferenceRequest] = Field(default_factory=list)
    linked_findings: list[DecisionFindingLinkRequest] = Field(default_factory=list)
    supersedes_decision_id: UUID | None = None


class DecisionWorkflowResponse(APIModel):
    case_id: UUID
    case_status: CaseStatus
    status_changed_at: datetime
    decision: DecisionResponse
    allowed_next_statuses: list[CaseStatus] = Field(default_factory=list)


class AuditEventResponse(APIModel):
    id: UUID
    case_id: UUID | None = None
    actor_user_id: UUID | None = None
    actor_type: AuditActorType
    actor_identifier: str | None = None
    event_type: AuditEventType
    summary: str
    resource_type: str
    resource_id: UUID
    occurred_at: datetime
    metadata: dict[str, object] = Field(default_factory=dict)
    evidence_refs: list[EvidenceReferenceResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class AuditEventListResponse(APIModel):
    items: list[AuditEventResponse] = Field(default_factory=list)
    total: int
    limit: int
    offset: int


class ManualReviewActionRequest(APIModel):
    performed_by_user_id: UUID
    action_type: ManualReviewActionType
    document_id: UUID | None = None
    related_decision_id: UUID | None = None
    comment: str | None = Field(default=None, max_length=4000)
    payload: dict[str, object] = Field(default_factory=dict)
    evidence_refs: list[EvidenceReferenceRequest] = Field(default_factory=list)


class ManualReviewActionResponse(APIModel):
    id: UUID
    case_id: UUID
    document_id: UUID | None = None
    performed_by_user_id: UUID
    related_decision_id: UUID | None = None
    action_type: ManualReviewActionType
    comment: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    evidence_refs: list[EvidenceReferenceResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ManualReviewCorrectionFieldRequest(APIModel):
    extraction_result_id: UUID
    field_name: str = Field(..., min_length=1, max_length=120)
    before_value: object | None = None
    after_value: object | None = None
    evidence_refs: list[EvidenceReferenceRequest] = Field(default_factory=list)


class ManualReviewCorrectionFieldResponse(APIModel):
    extraction_result_id: UUID
    field_name: str
    before_value: object | None = None
    after_value: object | None = None
    evidence_refs: list[EvidenceReferenceResponse] = Field(default_factory=list)


class RequireManualReviewRequest(APIModel):
    performed_by_user_id: UUID
    document_id: UUID | None = None
    comment: str | None = Field(default=None, max_length=4000)
    reason_code: str = Field(default="manual_review_required", min_length=1, max_length=100)
    evidence_refs: list[EvidenceReferenceRequest] = Field(default_factory=list)


class ManualReviewNoteRequest(APIModel):
    performed_by_user_id: UUID
    document_id: UUID | None = None
    comment: str = Field(..., min_length=1, max_length=4000)
    evidence_refs: list[EvidenceReferenceRequest] = Field(default_factory=list)


class ManualCorrectionSubmissionRequest(APIModel):
    performed_by_user_id: UUID
    document_id: UUID | None = None
    comment: str | None = Field(default=None, max_length=4000)
    corrections: list[ManualReviewCorrectionFieldRequest] = Field(default_factory=list, min_length=1)
    evidence_refs: list[EvidenceReferenceRequest] = Field(default_factory=list)


class ManualCorrectionSubmissionResponse(APIModel):
    case_id: UUID
    case_status: CaseStatus
    status_changed_at: datetime
    corrections: list[ManualReviewCorrectionFieldResponse] = Field(default_factory=list)
    action: ManualReviewActionResponse


class ManualReviewResubmitRequest(APIModel):
    performed_by_user_id: UUID
    document_id: UUID | None = None
    target_status: CaseStatus
    comment: str | None = Field(default=None, max_length=4000)
    reason_code: str | None = Field(default=None, max_length=100)
    evidence_refs: list[EvidenceReferenceRequest] = Field(default_factory=list)


class ManualReviewWorkflowResponse(APIModel):
    case_id: UUID
    case_status: CaseStatus
    status_changed_at: datetime
    allowed_next_statuses: list[CaseStatus] = Field(default_factory=list)
    action: ManualReviewActionResponse


class UpdateCaseStatusRequest(APIModel):
    target_status: CaseStatus
    actor_type: AuditActorType
    actor_id: str | None = None
    reason_code: str | None = Field(default=None, max_length=100)
    comment: str | None = Field(default=None, max_length=4000)
    metadata: dict[str, object] = Field(default_factory=dict)


class UpdateCaseStatusResponse(APIModel):
    id: UUID
    status: CaseStatus
    status_changed_at: datetime
    updated_at: datetime
    allowed_next_statuses: list[CaseStatus] = Field(default_factory=list)


class CaseDetailResponse(APIModel):
    id: UUID
    case_reference: str
    case_type: str
    status: CaseStatus
    status_changed_at: datetime
    current_queue: str
    source_channel: str
    customer_reference: str | None = None
    submitted_by_user: UserSummaryResponse | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    documents: list[DocumentUploadMetadataResponse] = Field(default_factory=list)
    ocr_results: list[OCRResultResponse] = Field(default_factory=list)
    extraction_results: list[ExtractionResultResponse] = Field(default_factory=list)
    validation: ValidationResultResponse
    decisions: list[DecisionResponse] = Field(default_factory=list)
    manual_review_actions: list[ManualReviewActionResponse] = Field(default_factory=list)
    audit_events: list[AuditEventResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None = None


class CaseListResponse(APIModel):
    items: list[CaseSummaryResponse] = Field(default_factory=list)
    total: int
    limit: int
    offset: int


class ErrorDetailResponse(APIModel):
    field: str | None = None
    issue: str
    context: dict[str, object] = Field(default_factory=dict)


class ErrorResponse(APIModel):
    code: str
    message: str
    trace_id: str | None = None
    details: list[ErrorDetailResponse] = Field(default_factory=list)

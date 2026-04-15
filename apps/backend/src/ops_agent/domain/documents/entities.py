from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from ops_agent.domain.shared.evidence import EvidenceRef
from ops_agent.domain.shared.enums import DocumentStatus, FindingSeverity, FindingStatus, ProcessingStatus, RiskLevel


@dataclass(slots=True, kw_only=True)
class Document:
    id: UUID
    case_id: UUID
    filename: str
    document_type: str
    mime_type: str
    storage_key: str
    sha256_digest: str
    status: DocumentStatus
    status_changed_at: datetime
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None
    source_channel: str = "manual_upload"
    page_count: int | None = None
    uploader_user_id: UUID | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True, kw_only=True)
class OCRResult:
    id: UUID
    document_id: UUID
    status: ProcessingStatus
    raw_text: str | None
    confidence_score: float | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None
    provider_name: str = "placeholder"
    provider_job_id: str | None = None
    processed_at: datetime | None = None
    page_count: int | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True, kw_only=True)
class ExtractionResult:
    id: UUID
    document_id: UUID
    status: ProcessingStatus
    schema_name: str
    extracted_payload: dict[str, object]
    confidence_score: float | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None
    ocr_result_id: UUID | None = None
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    provider_name: str = "placeholder"
    provider_job_id: str | None = None
    processed_at: datetime | None = None
    model_version: str | None = None


@dataclass(slots=True, kw_only=True)
class ValidationFinding:
    id: UUID
    case_id: UUID
    rule_code: str
    message: str
    severity: FindingSeverity
    status: FindingStatus
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None
    document_id: UUID | None = None
    extraction_result_id: UUID | None = None
    field_name: str | None = None
    resolution_note: str | None = None
    evidence_refs: list[EvidenceRef] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class RiskFinding:
    id: UUID
    case_id: UUID
    risk_code: str
    message: str
    risk_level: RiskLevel
    status: FindingStatus
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None
    document_id: UUID | None = None
    extraction_result_id: UUID | None = None
    risk_score: float | None = None
    evidence_refs: list[EvidenceRef] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class ComplianceFinding:
    id: UUID
    case_id: UUID
    policy_code: str
    message: str
    severity: FindingSeverity
    status: FindingStatus
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None
    document_id: UUID | None = None
    extraction_result_id: UUID | None = None
    regulation_reference: str | None = None
    evidence_refs: list[EvidenceRef] = field(default_factory=list)


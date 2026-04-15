from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID

from ops_agent.domain.shared.enums import DecisionOutcome, FindingSeverity, RiskLevel
from ops_agent.domain.shared.evidence import EvidenceRef


@dataclass(frozen=True, slots=True)
class OCRProviderRequest:
    case_id: UUID
    document_id: UUID
    filename: str
    mime_type: str
    content: bytes


@dataclass(frozen=True, slots=True)
class OCRProviderResult:
    raw_text: str
    confidence_score: float | None
    provider_name: str
    provider_job_id: str | None = None
    page_count: int | None = None
    evidence_refs: tuple[EvidenceRef, ...] = ()
    result_metadata: dict[str, str] = field(default_factory=dict)


class OCRProvider(Protocol):
    """Integration point for OCR providers."""

    def process(self, request: OCRProviderRequest) -> OCRProviderResult:
        """Synchronously process a document for MVP orchestration."""


@dataclass(frozen=True, slots=True)
class ExtractionProviderRequest:
    case_id: UUID
    document_id: UUID
    document_type: str
    filename: str
    raw_text: str


@dataclass(frozen=True, slots=True)
class ExtractionProviderResult:
    schema_name: str
    extracted_payload: dict[str, object]
    confidence_score: float | None
    evidence_refs: tuple[EvidenceRef, ...] = ()
    provider_name: str = "placeholder"
    provider_job_id: str | None = None
    model_version: str | None = None


class ExtractionProvider(Protocol):
    """Integration point for structured extraction providers."""

    def process(self, request: ExtractionProviderRequest) -> ExtractionProviderResult:
        """Synchronously produce structured document output for MVP orchestration."""


@dataclass(frozen=True, slots=True)
class DocumentClassificationProviderRequest:
    case_id: UUID
    document_id: UUID
    filename: str
    mime_type: str
    current_document_type: str | None
    raw_text: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DocumentClassificationProviderResult:
    document_type: str
    confidence_score: float | None
    evidence_refs: tuple[EvidenceRef, ...] = ()
    provider_name: str = "placeholder"
    provider_job_id: str | None = None
    classification_metadata: dict[str, str] = field(default_factory=dict)


class DocumentClassificationProvider(Protocol):
    """Integration point for document-type classification providers."""

    def process(self, request: DocumentClassificationProviderRequest) -> DocumentClassificationProviderResult:
        """Return a best-effort document class with confidence and supporting evidence."""


@dataclass(frozen=True, slots=True)
class ValidationDocumentContext:
    document_id: UUID
    extraction_result_id: UUID
    document_type: str
    filename: str
    raw_text: str
    ocr_confidence_score: float | None
    extracted_payload: dict[str, object]
    extraction_confidence_score: float | None
    evidence_refs: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidationFindingResult:
    document_id: UUID
    extraction_result_id: UUID
    rule_code: str
    message: str
    severity: FindingSeverity
    field_name: str | None = None
    evidence_refs: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True, slots=True)
class RiskFindingResult:
    document_id: UUID
    extraction_result_id: UUID
    risk_code: str
    message: str
    risk_level: RiskLevel
    evidence_refs: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True, slots=True)
class ComplianceFindingResult:
    document_id: UUID
    extraction_result_id: UUID
    policy_code: str
    message: str
    severity: FindingSeverity
    evidence_refs: tuple[EvidenceRef, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidationRulesEngineRequest:
    case_id: UUID
    documents: tuple[ValidationDocumentContext, ...]
    minimum_ocr_confidence: float
    minimum_extraction_confidence: float


@dataclass(frozen=True, slots=True)
class ValidationRulesEngineResult:
    validation_findings: tuple[ValidationFindingResult, ...] = ()
    risk_findings: tuple[RiskFindingResult, ...] = ()
    compliance_findings: tuple[ComplianceFindingResult, ...] = ()
    requires_manual_review: bool = False
    rationale: str = ""
    recommendation_reason_code: str = "system_recommendation_ready"
    recommendation_outcome: DecisionOutcome = DecisionOutcome.APPROVED


class ValidationRulesEngine(Protocol):
    """Integration point for deterministic rules engines and future policy services."""

    def evaluate(self, request: ValidationRulesEngineRequest) -> ValidationRulesEngineResult:
        """Evaluate extracted document data and produce structured findings."""

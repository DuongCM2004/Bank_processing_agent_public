from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ops_agent.domain.shared.enums import DocumentStatus, ProcessingStatus
from ops_agent.infrastructure.db.models.base import BaseModel, future_info, mvp_info


class Document(BaseModel):
    __tablename__ = "documents"
    __table_args__ = (Index("ix_documents_case_id_status", "case_id", "status"),)

    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        info=mvp_info("Owning case for the document and all downstream outputs."),
    )
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        info=mvp_info("Original filename captured at ingestion."),
    )
    document_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        info=mvp_info("Operations-assigned or upstream-provided document classification."),
    )
    mime_type: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        info=mvp_info("Uploaded document media type for safe handling."),
    )
    storage_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        info=mvp_info("Object storage reference for the source document."),
    )
    sha256_digest: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        info=mvp_info("Immutable content digest for deduplication and audit traceability."),
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False),
        nullable=False,
        default=DocumentStatus.UPLOADED,
        info=mvp_info("Current document processing state."),
    )
    status_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        info=mvp_info("Timestamp of the latest document status transition."),
    )
    source_channel: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="manual_upload",
        info=mvp_info("Ingestion source channel for the document."),
    )
    file_size_bytes: Mapped[int | None] = mapped_column(
        nullable=True,
        info=mvp_info("Uploaded file size in bytes for operational checks and traceability."),
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        info=mvp_info("Timestamp when the file was uploaded into managed storage."),
    )
    page_count: Mapped[int | None] = mapped_column(
        nullable=True,
        info=future_info("Derived page count once page-level processing is available."),
    )
    uploaded_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        info=future_info("Authenticated uploader reference for controlled submission channels."),
    )
    document_metadata: Mapped[dict[str, str]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        info=future_info("Supplemental document metadata such as source system references."),
    )

    case: Mapped["Case"] = relationship(back_populates="documents")
    uploaded_by_user: Mapped["User | None"] = relationship(back_populates="uploaded_documents")
    ocr_results: Mapped[list["OCRResult"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    extraction_results: Mapped[list["ExtractionResult"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
    validation_findings: Mapped[list["ValidationFinding"]] = relationship(back_populates="document")
    risk_findings: Mapped[list["RiskFinding"]] = relationship(back_populates="document")
    compliance_findings: Mapped[list["ComplianceFinding"]] = relationship(back_populates="document")
    manual_review_actions: Mapped[list["ManualReviewAction"]] = relationship(back_populates="document")


class OCRResult(BaseModel):
    __tablename__ = "ocr_results"
    __table_args__ = (Index("ix_ocr_results_document_status", "document_id", "status"),)

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        info=mvp_info("Source document from which OCR text was produced."),
    )
    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, native_enum=False),
        nullable=False,
        default=ProcessingStatus.PENDING,
        info=mvp_info("Explicit OCR processing state."),
    )
    raw_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        info=mvp_info("Raw OCR text output persisted for traceability and downstream parsing."),
    )
    confidence_score: Mapped[float | None] = mapped_column(
        nullable=True,
        info=mvp_info("Overall OCR confidence score when provided by the OCR engine."),
    )
    provider_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="placeholder",
        info=mvp_info("OCR provider identifier, placeholder or integrated."),
    )
    provider_job_id: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        info=future_info("Asynchronous provider job identifier for reconciliation."),
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        info=mvp_info("Timestamp when OCR processing completed or terminally failed."),
    )
    page_count: Mapped[int | None] = mapped_column(
        nullable=True,
        info=future_info("OCR-derived page count for page-level evidence UX."),
    )
    result_metadata: Mapped[dict[str, str]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        info=future_info("Provider-specific OCR metadata retained for diagnostics."),
    )

    document: Mapped[Document] = relationship(back_populates="ocr_results")
    extraction_results: Mapped[list["ExtractionResult"]] = relationship(back_populates="ocr_result")


class ExtractionResult(BaseModel):
    __tablename__ = "extraction_results"
    __table_args__ = (Index("ix_extraction_results_document_status", "document_id", "status"),)

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        info=mvp_info("Source document from which structured extraction was produced."),
    )
    ocr_result_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ocr_results.id", ondelete="SET NULL"),
        nullable=True,
        info=mvp_info("Optional OCR run used as the extraction input."),
    )
    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, native_enum=False),
        nullable=False,
        default=ProcessingStatus.PENDING,
        info=mvp_info("Explicit extraction processing state."),
    )
    schema_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        info=mvp_info("Extraction schema or template applied to the document."),
    )
    extracted_payload: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        info=mvp_info("Structured extraction output persisted for review and downstream validation."),
    )
    confidence_score: Mapped[float | None] = mapped_column(
        nullable=True,
        info=mvp_info("Aggregate extraction confidence score when available."),
    )
    evidence_refs: Mapped[list[dict[str, object]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        info=mvp_info("Evidence pointers linking extracted fields back to document locations."),
    )
    provider_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="placeholder",
        info=mvp_info("Extraction provider identifier."),
    )
    provider_job_id: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        info=future_info("Asynchronous provider job identifier for extraction engines."),
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        info=mvp_info("Timestamp when extraction processing completed or terminally failed."),
    )
    model_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        info=future_info("Model or prompt version used to generate the extraction output."),
    )

    document: Mapped[Document] = relationship(back_populates="extraction_results")
    ocr_result: Mapped[OCRResult | None] = relationship(back_populates="extraction_results")
    validation_findings: Mapped[list["ValidationFinding"]] = relationship(back_populates="extraction_result")
    risk_findings: Mapped[list["RiskFinding"]] = relationship(back_populates="extraction_result")
    compliance_findings: Mapped[list["ComplianceFinding"]] = relationship(back_populates="extraction_result")

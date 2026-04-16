from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedModel
from app.models.enums import DocumentStatus, ProcessingStatus

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.findings import ComplianceFinding, RiskFinding, ValidationFinding
    from app.models.manual_review import ManualReviewAction
    from app.models.user import User


class Document(TimestampedModel):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_case_id_status", "case_id", "status"),
        Index("ix_documents_sha256_digest", "sha256_digest"),
    )

    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(80), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    sha256_digest: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False),
        nullable=False,
        default=DocumentStatus.STORED,
    )
    status_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    source_channel: Mapped[str] = mapped_column(String(80), nullable=False, default="manual_upload")
    file_size_bytes: Mapped[int] = mapped_column(nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    uploaded_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    document_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    case: Mapped["Case"] = relationship(back_populates="documents")
    uploaded_by_user: Mapped["User | None"] = relationship(back_populates="uploaded_documents")
    ocr_results: Mapped[list["OCRResult"]] = relationship(back_populates="document")
    extraction_results: Mapped[list["ExtractionResult"]] = relationship(back_populates="document")
    validation_findings: Mapped[list["ValidationFinding"]] = relationship(back_populates="document")
    risk_findings: Mapped[list["RiskFinding"]] = relationship(back_populates="document")
    compliance_findings: Mapped[list["ComplianceFinding"]] = relationship(back_populates="document")
    manual_review_actions: Mapped[list["ManualReviewAction"]] = relationship(back_populates="document")


class OCRResult(TimestampedModel):
    __tablename__ = "ocr_results"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, native_enum=False),
        default=ProcessingStatus.PENDING,
    )
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(nullable=True)
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_job_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    document: Mapped[Document] = relationship(back_populates="ocr_results")
    extraction_results: Mapped[list["ExtractionResult"]] = relationship(back_populates="ocr_result")


class ExtractionResult(TimestampedModel):
    __tablename__ = "extraction_results"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    ocr_result_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ocr_results.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, native_enum=False),
        default=ProcessingStatus.PENDING,
    )
    schema_name: Mapped[str] = mapped_column(String(120), nullable=False)
    extracted_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    confidence_score: Mapped[float | None] = mapped_column(nullable=True)
    evidence_refs: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False, default=list)
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_job_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)

    document: Mapped[Document] = relationship(back_populates="extraction_results")
    ocr_result: Mapped[OCRResult | None] = relationship(back_populates="extraction_results")
    validation_findings: Mapped[list["ValidationFinding"]] = relationship(back_populates="extraction_result")
    risk_findings: Mapped[list["RiskFinding"]] = relationship(back_populates="extraction_result")
    compliance_findings: Mapped[list["ComplianceFinding"]] = relationship(back_populates="extraction_result")


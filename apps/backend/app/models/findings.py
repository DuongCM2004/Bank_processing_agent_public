from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedModel
from app.models.enums import FindingSeverity, FindingStatus, RiskLevel

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.document import Document, ExtractionResult


class ValidationFinding(TimestampedModel):
    __tablename__ = "validation_findings"

    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"))
    document_id: Mapped[UUID | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    extraction_result_id: Mapped[UUID | None] = mapped_column(ForeignKey("extraction_results.id"), nullable=True)
    rule_code: Mapped[str] = mapped_column(String(100))
    severity: Mapped[FindingSeverity] = mapped_column(Enum(FindingSeverity, native_enum=False))
    status: Mapped[FindingStatus] = mapped_column(
        Enum(FindingStatus, native_enum=False),
        default=FindingStatus.OPEN,
    )
    message: Mapped[str] = mapped_column(Text)
    evidence_refs: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False, default=list)

    case: Mapped["Case"] = relationship(back_populates="validation_findings")
    document: Mapped["Document | None"] = relationship(back_populates="validation_findings")
    extraction_result: Mapped["ExtractionResult | None"] = relationship(back_populates="validation_findings")


class RiskFinding(TimestampedModel):
    __tablename__ = "risk_findings"

    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"))
    document_id: Mapped[UUID | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    extraction_result_id: Mapped[UUID | None] = mapped_column(ForeignKey("extraction_results.id"), nullable=True)
    risk_code: Mapped[str] = mapped_column(String(100))
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel, native_enum=False))
    status: Mapped[FindingStatus] = mapped_column(
        Enum(FindingStatus, native_enum=False),
        default=FindingStatus.OPEN,
    )
    message: Mapped[str] = mapped_column(Text)
    evidence_refs: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False, default=list)

    case: Mapped["Case"] = relationship(back_populates="risk_findings")
    document: Mapped["Document | None"] = relationship(back_populates="risk_findings")
    extraction_result: Mapped["ExtractionResult | None"] = relationship(back_populates="risk_findings")


class ComplianceFinding(TimestampedModel):
    __tablename__ = "compliance_findings"

    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"))
    document_id: Mapped[UUID | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    extraction_result_id: Mapped[UUID | None] = mapped_column(ForeignKey("extraction_results.id"), nullable=True)
    control_code: Mapped[str] = mapped_column(String(100))
    severity: Mapped[FindingSeverity] = mapped_column(Enum(FindingSeverity, native_enum=False))
    status: Mapped[FindingStatus] = mapped_column(
        Enum(FindingStatus, native_enum=False),
        default=FindingStatus.OPEN,
    )
    message: Mapped[str] = mapped_column(Text)
    evidence_refs: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False, default=list)

    case: Mapped["Case"] = relationship(back_populates="compliance_findings")
    document: Mapped["Document | None"] = relationship(back_populates="compliance_findings")
    extraction_result: Mapped["ExtractionResult | None"] = relationship(back_populates="compliance_findings")


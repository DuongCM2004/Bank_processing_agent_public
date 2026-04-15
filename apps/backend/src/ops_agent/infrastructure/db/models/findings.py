from __future__ import annotations

from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ops_agent.domain.shared.enums import FindingSeverity, FindingStatus, RiskLevel
from ops_agent.infrastructure.db.models.base import BaseModel, future_info, mvp_info


class ValidationFinding(BaseModel):
    __tablename__ = "validation_findings"
    __table_args__ = (Index("ix_validation_findings_case_status", "case_id", "status"),)

    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        info=mvp_info("Owning case for the validation issue."),
    )
    document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        info=mvp_info("Optional source document where the issue was detected."),
    )
    extraction_result_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("extraction_results.id", ondelete="SET NULL"),
        nullable=True,
        info=mvp_info("Optional extraction output that triggered the finding."),
    )
    rule_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        info=mvp_info("Validation rule identifier."),
    )
    field_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        info=mvp_info("Structured field implicated by the validation issue."),
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        info=mvp_info("Human-readable validation issue description."),
    )
    severity: Mapped[FindingSeverity] = mapped_column(
        Enum(FindingSeverity, native_enum=False),
        nullable=False,
        info=mvp_info("Validation issue severity used for routing."),
    )
    status: Mapped[FindingStatus] = mapped_column(
        Enum(FindingStatus, native_enum=False),
        nullable=False,
        default=FindingStatus.OPEN,
        info=mvp_info("Operational finding lifecycle state."),
    )
    resolution_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        info=future_info("Resolution explanation recorded by reviewers or automated handlers."),
    )
    evidence_refs: Mapped[list[dict[str, object]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        info=mvp_info("Evidence pointers supporting the finding."),
    )

    case: Mapped["Case"] = relationship(back_populates="validation_findings")
    document: Mapped["Document | None"] = relationship(back_populates="validation_findings")
    extraction_result: Mapped["ExtractionResult | None"] = relationship(back_populates="validation_findings")


class RiskFinding(BaseModel):
    __tablename__ = "risk_findings"
    __table_args__ = (Index("ix_risk_findings_case_status", "case_id", "status"),)

    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        info=mvp_info("Owning case for the risk issue."),
    )
    document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        info=mvp_info("Optional source document for the detected risk."),
    )
    extraction_result_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("extraction_results.id", ondelete="SET NULL"),
        nullable=True,
        info=mvp_info("Optional extraction output that surfaced the risk."),
    )
    risk_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        info=mvp_info("Risk rule or typology code."),
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        info=mvp_info("Human-readable risk description."),
    )
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, native_enum=False),
        nullable=False,
        info=mvp_info("Risk severity used for escalation and review routing."),
    )
    risk_score: Mapped[float | None] = mapped_column(
        nullable=True,
        info=future_info("Continuous risk score when a scoring engine is introduced."),
    )
    status: Mapped[FindingStatus] = mapped_column(
        Enum(FindingStatus, native_enum=False),
        nullable=False,
        default=FindingStatus.OPEN,
        info=mvp_info("Operational finding lifecycle state."),
    )
    evidence_refs: Mapped[list[dict[str, object]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        info=mvp_info("Evidence pointers supporting the risk finding."),
    )

    case: Mapped["Case"] = relationship(back_populates="risk_findings")
    document: Mapped["Document | None"] = relationship(back_populates="risk_findings")
    extraction_result: Mapped["ExtractionResult | None"] = relationship(back_populates="risk_findings")


class ComplianceFinding(BaseModel):
    __tablename__ = "compliance_findings"
    __table_args__ = (Index("ix_compliance_findings_case_status", "case_id", "status"),)

    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        info=mvp_info("Owning case for the compliance issue."),
    )
    document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        info=mvp_info("Optional source document for the compliance issue."),
    )
    extraction_result_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("extraction_results.id", ondelete="SET NULL"),
        nullable=True,
        info=mvp_info("Optional extraction output that triggered the compliance issue."),
    )
    policy_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        info=mvp_info("Compliance policy or control identifier."),
    )
    regulation_reference: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        info=future_info("Mapped regulation citation or control library reference."),
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        info=mvp_info("Human-readable compliance issue description."),
    )
    severity: Mapped[FindingSeverity] = mapped_column(
        Enum(FindingSeverity, native_enum=False),
        nullable=False,
        info=mvp_info("Compliance issue severity used for routing and approval controls."),
    )
    status: Mapped[FindingStatus] = mapped_column(
        Enum(FindingStatus, native_enum=False),
        nullable=False,
        default=FindingStatus.OPEN,
        info=mvp_info("Operational finding lifecycle state."),
    )
    evidence_refs: Mapped[list[dict[str, object]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        info=mvp_info("Evidence pointers supporting the compliance issue."),
    )

    case: Mapped["Case"] = relationship(back_populates="compliance_findings")
    document: Mapped["Document | None"] = relationship(back_populates="compliance_findings")
    extraction_result: Mapped["ExtractionResult | None"] = relationship(back_populates="compliance_findings")

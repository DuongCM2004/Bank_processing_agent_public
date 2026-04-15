from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ops_agent.domain.shared.enums import CaseStatus
from ops_agent.infrastructure.db.models.base import BaseModel, future_info, mvp_info


class Case(BaseModel):
    __tablename__ = "cases"
    __table_args__ = (
        UniqueConstraint("case_reference", name="uq_cases_case_reference"),
        Index("ix_cases_status", "status"),
    )

    case_reference: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        info=mvp_info("Stable business reference visible to operations teams."),
    )
    case_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        info=mvp_info("Workflow or product type controlling downstream processing."),
    )
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, native_enum=False),
        nullable=False,
        default=CaseStatus.CREATED,
        info=mvp_info("Current explicit workflow state of the case."),
    )
    status_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        info=mvp_info("Timestamp of the latest case status transition."),
    )
    current_queue: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="document_ops",
        info=mvp_info("Current operational queue owning the case."),
    )
    source_channel: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="manual_upload",
        info=mvp_info("Ingestion source used for routing and audit context."),
    )
    customer_reference: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        info=future_info("External customer or account identifier when enabled."),
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        info=future_info("Terminal timestamp when the case is operationally closed."),
    )
    submitted_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        info=future_info("Originating authenticated user when submissions are user-linked."),
    )
    case_metadata: Mapped[dict[str, str]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        info=future_info("Supplemental case metadata and integration context."),
    )

    submitted_by_user: Mapped["User | None"] = relationship(back_populates="submitted_cases")
    documents: Mapped[list["Document"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    validation_findings: Mapped[list["ValidationFinding"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    risk_findings: Mapped[list["RiskFinding"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    compliance_findings: Mapped[list["ComplianceFinding"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    decisions: Mapped[list["Decision"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    manual_review_actions: Mapped[list["ManualReviewAction"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="case", cascade="all, delete-orphan")

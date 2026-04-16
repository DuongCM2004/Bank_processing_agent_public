from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedModel
from app.models.enums import CaseStatus

if TYPE_CHECKING:
    from app.models.audit_event import AuditEvent
    from app.models.decision import Decision
    from app.models.document import Document
    from app.models.findings import ComplianceFinding, RiskFinding, ValidationFinding
    from app.models.manual_review import ManualReviewAction
    from app.models.user import User


class Case(TimestampedModel):
    __tablename__ = "cases"
    __table_args__ = (
        Index("ix_cases_status", "status"),
        Index("ix_cases_queue_status", "current_queue", "status"),
    )

    case_reference: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    case_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, native_enum=False),
        nullable=False,
        default=CaseStatus.CREATED,
    )
    status_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    current_queue: Mapped[str] = mapped_column(String(80), nullable=False, default="document_ops")
    source_channel: Mapped[str] = mapped_column(String(80), nullable=False, default="manual_upload")
    customer_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    submitted_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    case_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    submitted_by_user: Mapped["User | None"] = relationship(back_populates="submitted_cases")
    documents: Mapped[list["Document"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    validation_findings: Mapped[list["ValidationFinding"]] = relationship(back_populates="case")
    risk_findings: Mapped[list["RiskFinding"]] = relationship(back_populates="case")
    compliance_findings: Mapped[list["ComplianceFinding"]] = relationship(back_populates="case")
    decisions: Mapped[list["Decision"]] = relationship(back_populates="case")
    manual_review_actions: Mapped[list["ManualReviewAction"]] = relationship(back_populates="case")
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="case")


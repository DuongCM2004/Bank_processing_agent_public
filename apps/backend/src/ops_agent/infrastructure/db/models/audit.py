from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ops_agent.domain.shared.enums import AuditActorType, AuditEventType
from ops_agent.infrastructure.db.models.base import BaseModel, mvp_info


class AuditEvent(BaseModel):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_case_id_occurred_at", "case_id", "occurred_at"),
        Index("ix_audit_events_case_id_event_type", "case_id", "event_type"),
        Index("ix_audit_events_resource_type_resource_id", "resource_type", "resource_id"),
    )

    case_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=True,
        info=mvp_info("Owning case when the event is case-scoped."),
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        info=mvp_info("Human actor when the event originates from a user."),
    )
    actor_type: Mapped[AuditActorType] = mapped_column(
        Enum(AuditActorType, native_enum=False),
        nullable=False,
        info=mvp_info("Actor category for the audit event."),
    )
    actor_identifier: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        info=mvp_info("Service name, username, or system identifier for the actor."),
    )
    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType, native_enum=False),
        nullable=False,
        info=mvp_info("High-level audit event classification."),
    )
    summary: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
        info=mvp_info("Human-readable summary distinct from application logs."),
    )
    resource_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        info=mvp_info("Resource type affected by the event."),
    )
    resource_id: Mapped[UUID] = mapped_column(
        Uuid,
        nullable=False,
        info=mvp_info("Resource identifier affected by the event."),
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        info=mvp_info("Business timestamp when the audited action occurred."),
    )
    details: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        info=mvp_info("Structured event payload for forensic traceability."),
    )
    evidence_refs: Mapped[list[dict[str, object]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        info=mvp_info("Evidence pointers recorded with the audit event."),
    )

    case: Mapped["Case | None"] = relationship(back_populates="audit_events")
    actor_user: Mapped["User | None"] = relationship(back_populates="audit_events")

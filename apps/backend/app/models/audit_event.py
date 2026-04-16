from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedModel
from app.models.enums import AuditActorType, AuditEventType

if TYPE_CHECKING:
    from app.models.case import Case


class AuditEvent(TimestampedModel):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_case_id_created_at", "case_id", "created_at"),)

    case_id: Mapped[UUID | None] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=True)
    event_type: Mapped[AuditEventType] = mapped_column(Enum(AuditEventType, native_enum=False))
    actor_type: Mapped[AuditActorType] = mapped_column(Enum(AuditActorType, native_enum=False))
    actor_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    case: Mapped["Case | None"] = relationship(back_populates="audit_events")


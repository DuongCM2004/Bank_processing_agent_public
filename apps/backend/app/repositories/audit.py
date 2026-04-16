from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


class AuditEventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, event: AuditEvent) -> AuditEvent:
        self.db.add(event)
        return event

    def list_for_case(self, case_id: UUID, *, limit: int = 100, offset: int = 0) -> tuple[list[AuditEvent], int]:
        total = self.db.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.case_id == case_id)) or 0
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.case_id == case_id)
            .order_by(AuditEvent.occurred_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(stmt)), total


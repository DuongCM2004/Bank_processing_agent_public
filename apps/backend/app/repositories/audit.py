from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
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

    def list_for_uuid(self, entity_uuid: UUID, *, limit: int = 100, offset: int = 0) -> tuple[list[AuditEvent], int]:
        entity_id = str(entity_uuid)
        predicate = or_(AuditEvent.case_id == entity_uuid, AuditEvent.entity_id == entity_id)
        total = self.db.scalar(select(func.count()).select_from(AuditEvent).where(predicate)) or 0
        stmt = (
            select(AuditEvent)
            .where(predicate)
            .order_by(AuditEvent.occurred_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(stmt)), total

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ops_agent.domain.shared.enums import AuditActorType, AuditEventType
from ops_agent.infrastructure.db.models import AuditEvent, Case


@dataclass(slots=True)
class AuditEventFilters:
    event_type: AuditEventType | None = None
    actor_type: AuditActorType | None = None
    resource_type: str | None = None


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_event(self, event: AuditEvent) -> AuditEvent:
        self._session.add(event)
        return event

    def case_exists(self, case_id: UUID) -> bool:
        statement = select(Case.id).where(Case.id == case_id)
        return self._session.execute(statement).scalar_one_or_none() is not None

    def list_case_events(
        self,
        *,
        case_id: UUID,
        filters: AuditEventFilters,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditEvent], int]:
        statement = select(AuditEvent).where(AuditEvent.case_id == case_id).order_by(AuditEvent.occurred_at.desc(), AuditEvent.created_at.desc())
        count_statement = select(func.count()).select_from(AuditEvent).where(AuditEvent.case_id == case_id)

        if filters.event_type is not None:
            statement = statement.where(AuditEvent.event_type == filters.event_type)
            count_statement = count_statement.where(AuditEvent.event_type == filters.event_type)
        if filters.actor_type is not None:
            statement = statement.where(AuditEvent.actor_type == filters.actor_type)
            count_statement = count_statement.where(AuditEvent.actor_type == filters.actor_type)
        if filters.resource_type:
            statement = statement.where(AuditEvent.resource_type == filters.resource_type)
            count_statement = count_statement.where(AuditEvent.resource_type == filters.resource_type)

        statement = statement.limit(limit).offset(offset)
        items = list(self._session.execute(statement).scalars().all())
        total = int(self._session.execute(count_statement).scalar_one())
        return items, total

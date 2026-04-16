from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from app.models.audit_event import AuditEvent
from app.models.enums import AuditActorType, AuditEventType
from app.repositories.audit import AuditEventRepository


class AuditLogger:
    def __init__(self, repository: AuditEventRepository) -> None:
        self.repository = repository

    def record(
        self,
        *,
        event_type: AuditEventType,
        actor_type: AuditActorType,
        entity_type: str,
        message: str,
        case_id: UUID | None = None,
        actor_id: str | None = None,
        entity_id: UUID | str | None = None,
        details: dict[str, object] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            case_id=case_id,
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            occurred_at=datetime.now(UTC),
            message=message,
            details=details or {},
        )
        return self.repository.add(event)


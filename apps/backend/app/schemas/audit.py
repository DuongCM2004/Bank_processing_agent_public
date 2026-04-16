from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.models.enums import AuditActorType, AuditEventType
from app.schemas.common import APIModel


class AuditEventResponse(APIModel):
    id: UUID
    case_id: UUID | None
    event_type: AuditEventType
    actor_type: AuditActorType
    actor_id: str | None
    entity_type: str
    entity_id: str | None
    occurred_at: datetime
    message: str
    details: dict[str, object]


class AuditEventListResponse(APIModel):
    items: list[AuditEventResponse]
    total: int


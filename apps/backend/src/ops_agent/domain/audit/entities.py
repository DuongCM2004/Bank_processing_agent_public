from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from ops_agent.domain.shared.evidence import EvidenceRef
from ops_agent.domain.shared.enums import AuditActorType, AuditEventType


@dataclass(slots=True, kw_only=True)
class AuditEvent:
    id: UUID
    event_type: AuditEventType
    actor_type: AuditActorType
    resource_type: str
    resource_id: UUID
    occurred_at: datetime
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None
    case_id: UUID | None = None
    actor_user_id: UUID | None = None
    actor_identifier: str | None = None
    details: dict[str, object] = field(default_factory=dict)
    evidence_refs: list[EvidenceRef] = field(default_factory=list)


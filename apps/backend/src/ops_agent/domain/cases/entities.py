from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from ops_agent.domain.shared.enums import CaseStatus


@dataclass(slots=True, kw_only=True)
class Case:
    id: UUID
    case_reference: str
    case_type: str
    status: CaseStatus
    status_changed_at: datetime
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None
    current_queue: str = "document_ops"
    source_channel: str = "manual_upload"
    customer_reference: str | None = None
    closed_at: datetime | None = None
    submitted_by_user_id: UUID | None = None
    metadata: dict[str, str] = field(default_factory=dict)


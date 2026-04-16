from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.enums import AuditActorType, CaseStatus
from app.schemas.common import APIModel


class CaseCreateRequest(APIModel):
    case_reference: str = Field(max_length=64)
    case_type: str = Field(max_length=80)
    customer_reference: str | None = Field(default=None, max_length=120)
    source_channel: str = Field(default="manual_upload", max_length=80)
    current_queue: str = Field(default="document_ops", max_length=80)
    case_metadata: dict[str, object] = Field(default_factory=dict)
    actor_id: str | None = Field(default=None, max_length=128)


class CaseResponse(APIModel):
    id: UUID
    case_reference: str
    case_type: str
    status: CaseStatus
    status_changed_at: datetime
    current_queue: str
    source_channel: str
    customer_reference: str | None
    case_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class CaseListResponse(APIModel):
    items: list[CaseResponse]
    total: int
    limit: int
    offset: int


class CaseStatusTransitionRequest(APIModel):
    to_status: CaseStatus
    actor_type: AuditActorType = AuditActorType.USER
    actor_id: str | None = Field(default=None, max_length=128)
    reason_code: str | None = Field(default=None, max_length=100)
    comment: str | None = Field(default=None, max_length=500)
    metadata: dict[str, object] = Field(default_factory=dict)


class CaseStatusTransitionResponse(APIModel):
    case_id: UUID
    from_status: CaseStatus
    to_status: CaseStatus
    transition_name: str
    status_changed_at: datetime


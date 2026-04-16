from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AuditActorType


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ActorContext(APIModel):
    actor_type: AuditActorType = AuditActorType.USER
    actor_id: str | None = Field(default=None, max_length=128)


class EvidenceRef(APIModel):
    document_id: UUID | None = None
    page_number: int | None = Field(default=None, ge=1)
    field_name: str | None = Field(default=None, max_length=120)
    excerpt: str | None = Field(default=None, max_length=500)
    bounding_box: dict[str, float] | None = None


class TimestampedResponse(APIModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


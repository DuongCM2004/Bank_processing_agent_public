from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.models.enums import ManualReviewActionType
from app.schemas.common import APIModel, EvidenceRef, TimestampedResponse


class ManualReviewActionCreateRequest(APIModel):
    document_id: UUID | None = None
    action_type: ManualReviewActionType
    reviewer_id: str = Field(max_length=128)
    comment: str | None = Field(default=None, max_length=1000)
    payload: dict[str, object] = Field(default_factory=dict)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


class ManualReviewActionResponse(TimestampedResponse):
    case_id: UUID
    document_id: UUID | None
    action_type: ManualReviewActionType
    reviewer_id: str
    comment: str | None
    payload: dict[str, object]
    evidence_refs: list[dict[str, object]]


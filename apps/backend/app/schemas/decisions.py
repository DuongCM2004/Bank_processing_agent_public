from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.models.enums import DecisionOutcome
from app.schemas.common import APIModel, EvidenceRef, TimestampedResponse


class DecisionCreateRequest(APIModel):
    outcome: DecisionOutcome
    rationale: str = Field(min_length=1)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    decision_metadata: dict[str, object] = Field(default_factory=dict)
    actor_id: str = Field(max_length=128)


class DecisionResponse(TimestampedResponse):
    case_id: UUID
    outcome: DecisionOutcome
    decided_by: str
    rationale: str
    evidence_refs: list[dict[str, object]]
    decision_metadata: dict[str, object]


from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from ops_agent.domain.shared.evidence import EvidenceRef
from ops_agent.domain.shared.enums import DecisionOutcome, DecisionType, ManualReviewActionType, RoleCode, UserStatus


@dataclass(slots=True, kw_only=True)
class Role:
    id: UUID
    code: RoleCode
    name: str
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None
    description: str | None = None


@dataclass(slots=True, kw_only=True)
class User:
    id: UUID
    username: str
    email: str
    display_name: str
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None
    role_ids: list[UUID] = field(default_factory=list)
    last_login_at: datetime | None = None


@dataclass(slots=True, kw_only=True)
class Decision:
    id: UUID
    case_id: UUID
    decision_type: DecisionType
    outcome: DecisionOutcome
    reason_code: str
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None
    decided_by_user_id: UUID | None = None
    rationale: str | None = None
    confidence_score: float | None = None
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    supersedes_decision_id: UUID | None = None


@dataclass(slots=True, kw_only=True)
class ManualReviewAction:
    id: UUID
    case_id: UUID
    performed_by_user_id: UUID
    action_type: ManualReviewActionType
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None
    document_id: UUID | None = None
    related_decision_id: UUID | None = None
    comment: str | None = None
    payload: dict[str, object] = field(default_factory=dict)
    evidence_refs: list[EvidenceRef] = field(default_factory=list)


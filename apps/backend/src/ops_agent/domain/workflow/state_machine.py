from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from ops_agent.domain.shared.enums import AuditActorType, AuditEventType, CaseStatus
from ops_agent.domain.shared.exceptions import ConflictError


@dataclass(frozen=True, slots=True)
class CaseTransitionRule:
    from_status: CaseStatus
    to_status: CaseStatus
    transition_name: str
    reason_code: str
    audit_event_type: AuditEventType = AuditEventType.STATUS_CHANGED


@dataclass(frozen=True, slots=True)
class CaseTransitionContext:
    actor_type: AuditActorType
    actor_id: str | None = None
    reason_code: str | None = None
    comment: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class CaseTransitionAuditRecord:
    case_id: UUID
    from_status: CaseStatus
    to_status: CaseStatus
    transition_name: str
    actor_type: AuditActorType
    actor_id: str | None
    reason_code: str
    comment: str | None
    metadata: dict[str, object]
    occurred_at: datetime
    event_type: AuditEventType = AuditEventType.STATUS_CHANGED


class CaseTransitionAuditHook(Protocol):
    def record_transition(self, event: CaseTransitionAuditRecord) -> None:
        """Persist or emit a case transition audit record."""


class CaseStatusCarrier(Protocol):
    id: UUID
    status: CaseStatus
    status_changed_at: datetime
    updated_at: datetime
    updated_by: str | None


class InvalidCaseTransitionError(ConflictError):
    def __init__(
        self,
        *,
        case_id: UUID,
        from_status: CaseStatus,
        to_status: CaseStatus,
        allowed_statuses: tuple[CaseStatus, ...],
    ) -> None:
        allowed = ", ".join(status.value for status in allowed_statuses) or "none"
        message = (
            f"Cannot transition case {case_id} from '{from_status.value}' to '{to_status.value}'. "
            f"Allowed target states: {allowed}."
        )
        super().__init__(message, error_code="invalid_case_transition")
        self.case_id = case_id
        self.from_status = from_status
        self.to_status = to_status
        self.allowed_statuses = allowed_statuses


class CaseWorkflowStateMachine:
    def __init__(self, rules: list[CaseTransitionRule]) -> None:
        self._rules = rules
        self._by_from_status: dict[CaseStatus, dict[CaseStatus, CaseTransitionRule]] = {}
        for rule in rules:
            self._by_from_status.setdefault(rule.from_status, {})[rule.to_status] = rule

    @classmethod
    def default(cls) -> "CaseWorkflowStateMachine":
        return cls(
            rules=[
                CaseTransitionRule(
                    CaseStatus.CREATED,
                    CaseStatus.DOCUMENTS_UPLOADED,
                    "documents_registered",
                    "documents_uploaded",
                ),
                CaseTransitionRule(
                    CaseStatus.DOCUMENTS_UPLOADED,
                    CaseStatus.QUEUED_FOR_PROCESSING,
                    "queue_for_processing",
                    "queued_for_processing",
                ),
                CaseTransitionRule(
                    CaseStatus.QUEUED_FOR_PROCESSING,
                    CaseStatus.PROCESSING,
                    "start_processing",
                    "processing_started",
                ),
                CaseTransitionRule(
                    CaseStatus.PROCESSING,
                    CaseStatus.EXTRACTION_COMPLETED,
                    "mark_extraction_completed",
                    "extraction_completed",
                    audit_event_type=AuditEventType.EXTRACTION_COMPLETED,
                ),
                CaseTransitionRule(
                    CaseStatus.EXTRACTION_COMPLETED,
                    CaseStatus.VALIDATION_COMPLETED,
                    "mark_validation_completed",
                    "validation_completed",
                ),
                CaseTransitionRule(
                    CaseStatus.VALIDATION_COMPLETED,
                    CaseStatus.MANUAL_REVIEW_REQUIRED,
                    "request_manual_review",
                    "manual_review_required",
                ),
                CaseTransitionRule(
                    CaseStatus.VALIDATION_COMPLETED,
                    CaseStatus.DECISION_READY,
                    "mark_decision_ready",
                    "decision_ready",
                ),
                CaseTransitionRule(
                    CaseStatus.MANUAL_REVIEW_REQUIRED,
                    CaseStatus.DECISION_READY,
                    "complete_manual_review",
                    "manual_review_completed",
                ),
                CaseTransitionRule(
                    CaseStatus.DECISION_READY,
                    CaseStatus.MANUAL_REVIEW_REQUIRED,
                    "reopen_for_manual_review",
                    "manual_review_required",
                ),
                CaseTransitionRule(
                    CaseStatus.MANUAL_REVIEW_REQUIRED,
                    CaseStatus.QUEUED_FOR_PROCESSING,
                    "request_reprocessing",
                    "manual_reprocessing_requested",
                ),
                CaseTransitionRule(
                    CaseStatus.DECISION_READY,
                    CaseStatus.APPROVED,
                    "approve_case",
                    "case_approved",
                ),
                CaseTransitionRule(
                    CaseStatus.DECISION_READY,
                    CaseStatus.REJECTED,
                    "reject_case",
                    "case_rejected",
                ),
                CaseTransitionRule(
                    CaseStatus.DOCUMENTS_UPLOADED,
                    CaseStatus.FAILED,
                    "fail_case",
                    "document_intake_failed",
                ),
                CaseTransitionRule(
                    CaseStatus.QUEUED_FOR_PROCESSING,
                    CaseStatus.FAILED,
                    "fail_case",
                    "queue_dispatch_failed",
                ),
                CaseTransitionRule(
                    CaseStatus.PROCESSING,
                    CaseStatus.FAILED,
                    "fail_case",
                    "processing_failed",
                ),
                CaseTransitionRule(
                    CaseStatus.EXTRACTION_COMPLETED,
                    CaseStatus.FAILED,
                    "fail_case",
                    "post_extraction_failed",
                ),
                CaseTransitionRule(
                    CaseStatus.VALIDATION_COMPLETED,
                    CaseStatus.FAILED,
                    "fail_case",
                    "validation_failed",
                ),
                CaseTransitionRule(
                    CaseStatus.MANUAL_REVIEW_REQUIRED,
                    CaseStatus.FAILED,
                    "fail_case",
                    "manual_review_failed",
                ),
                CaseTransitionRule(
                    CaseStatus.FAILED,
                    CaseStatus.QUEUED_FOR_PROCESSING,
                    "retry_case",
                    "manual_retry_requested",
                ),
            ]
        )

    @property
    def rules(self) -> tuple[CaseTransitionRule, ...]:
        return tuple(self._rules)

    def allowed_transitions(self) -> dict[CaseStatus, tuple[CaseStatus, ...]]:
        return {
            source: tuple(targets.keys())
            for source, targets in self._by_from_status.items()
        }

    def next_statuses(self, from_status: CaseStatus) -> tuple[CaseStatus, ...]:
        return tuple(self._by_from_status.get(from_status, {}).keys())

    def can_transition(self, from_status: CaseStatus, to_status: CaseStatus) -> bool:
        return to_status in self._by_from_status.get(from_status, {})

    def validate_transition(self, *, case_id: UUID, from_status: CaseStatus, to_status: CaseStatus) -> CaseTransitionRule:
        if from_status == to_status:
            raise InvalidCaseTransitionError(
                case_id=case_id,
                from_status=from_status,
                to_status=to_status,
                allowed_statuses=self.next_statuses(from_status),
            )

        rule = self._by_from_status.get(from_status, {}).get(to_status)
        if rule is None:
            raise InvalidCaseTransitionError(
                case_id=case_id,
                from_status=from_status,
                to_status=to_status,
                allowed_statuses=self.next_statuses(from_status),
            )
        return rule


def transition_case_status(
    *,
    case: CaseStatusCarrier,
    to_status: CaseStatus,
    context: CaseTransitionContext,
    state_machine: CaseWorkflowStateMachine | None = None,
    audit_hooks: tuple[CaseTransitionAuditHook, ...] = (),
) -> CaseTransitionRule:
    machine = state_machine or CaseWorkflowStateMachine.default()
    rule = machine.validate_transition(case_id=case.id, from_status=case.status, to_status=to_status)

    case.status = to_status
    case.status_changed_at = context.occurred_at
    case.updated_at = context.occurred_at
    case.updated_by = context.actor_id

    audit_event = CaseTransitionAuditRecord(
        case_id=case.id,
        from_status=rule.from_status,
        to_status=rule.to_status,
        transition_name=rule.transition_name,
        actor_type=context.actor_type,
        actor_id=context.actor_id,
        reason_code=context.reason_code or rule.reason_code,
        comment=context.comment,
        metadata=context.metadata,
        occurred_at=context.occurred_at,
        event_type=rule.audit_event_type,
    )
    for hook in audit_hooks:
        hook.record_transition(audit_event)

    return rule

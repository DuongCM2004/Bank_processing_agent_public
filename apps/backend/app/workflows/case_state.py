from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from app.core.exceptions import ConflictError
from app.models.enums import AuditActorType, CaseStatus


@dataclass(frozen=True, slots=True)
class CaseTransitionRule:
    from_status: CaseStatus
    to_status: CaseStatus
    transition_name: str
    reason_code: str


@dataclass(frozen=True, slots=True)
class CaseTransitionContext:
    actor_type: AuditActorType
    actor_id: str | None = None
    reason_code: str | None = None
    comment: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


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
        super().__init__(
            f"Cannot transition case {case_id} from '{from_status.value}' to "
            f"'{to_status.value}'. Allowed target states: {allowed}.",
            error_code="invalid_case_transition",
        )


class CaseWorkflowStateMachine:
    def __init__(self, rules: tuple[CaseTransitionRule, ...]) -> None:
        self._rules = rules
        self._rules_by_source = {
            source: {rule.to_status: rule for rule in rules if rule.from_status == source}
            for source in CaseStatus
        }

    @classmethod
    def default(cls) -> "CaseWorkflowStateMachine":
        return cls(
            (
                CaseTransitionRule(CaseStatus.CREATED, CaseStatus.DOCUMENTS_UPLOADED, "documents_registered", "documents_uploaded"),
                CaseTransitionRule(CaseStatus.DOCUMENTS_UPLOADED, CaseStatus.QUEUED_FOR_PROCESSING, "queue_for_processing", "queued_for_processing"),
                CaseTransitionRule(CaseStatus.QUEUED_FOR_PROCESSING, CaseStatus.PROCESSING, "start_processing", "processing_started"),
                CaseTransitionRule(CaseStatus.PROCESSING, CaseStatus.EXTRACTION_COMPLETED, "mark_extraction_completed", "extraction_completed"),
                CaseTransitionRule(CaseStatus.EXTRACTION_COMPLETED, CaseStatus.VALIDATION_COMPLETED, "mark_validation_completed", "validation_completed"),
                CaseTransitionRule(CaseStatus.VALIDATION_COMPLETED, CaseStatus.MANUAL_REVIEW_REQUIRED, "request_manual_review", "manual_review_required"),
                CaseTransitionRule(CaseStatus.VALIDATION_COMPLETED, CaseStatus.DECISION_READY, "mark_decision_ready", "decision_ready"),
                CaseTransitionRule(CaseStatus.MANUAL_REVIEW_REQUIRED, CaseStatus.DECISION_READY, "complete_manual_review", "manual_review_completed"),
                CaseTransitionRule(CaseStatus.DECISION_READY, CaseStatus.MANUAL_REVIEW_REQUIRED, "reopen_for_manual_review", "manual_review_required"),
                CaseTransitionRule(CaseStatus.MANUAL_REVIEW_REQUIRED, CaseStatus.QUEUED_FOR_PROCESSING, "request_reprocessing", "manual_reprocessing_requested"),
                CaseTransitionRule(CaseStatus.DECISION_READY, CaseStatus.APPROVED, "approve_case", "case_approved"),
                CaseTransitionRule(CaseStatus.DECISION_READY, CaseStatus.REJECTED, "reject_case", "case_rejected"),
                CaseTransitionRule(CaseStatus.DOCUMENTS_UPLOADED, CaseStatus.FAILED, "fail_case", "document_intake_failed"),
                CaseTransitionRule(CaseStatus.QUEUED_FOR_PROCESSING, CaseStatus.FAILED, "fail_case", "queue_dispatch_failed"),
                CaseTransitionRule(CaseStatus.PROCESSING, CaseStatus.FAILED, "fail_case", "processing_failed"),
                CaseTransitionRule(CaseStatus.EXTRACTION_COMPLETED, CaseStatus.FAILED, "fail_case", "post_extraction_failed"),
                CaseTransitionRule(CaseStatus.VALIDATION_COMPLETED, CaseStatus.FAILED, "fail_case", "validation_failed"),
                CaseTransitionRule(CaseStatus.MANUAL_REVIEW_REQUIRED, CaseStatus.FAILED, "fail_case", "manual_review_failed"),
                CaseTransitionRule(CaseStatus.FAILED, CaseStatus.QUEUED_FOR_PROCESSING, "retry_case", "manual_retry_requested"),
            )
        )

    def next_statuses(self, from_status: CaseStatus) -> tuple[CaseStatus, ...]:
        return tuple(self._rules_by_source.get(from_status, {}).keys())

    def validate(self, *, case_id: UUID, from_status: CaseStatus, to_status: CaseStatus) -> CaseTransitionRule:
        rule = self._rules_by_source.get(from_status, {}).get(to_status)
        if rule is None:
            raise InvalidCaseTransitionError(
                case_id=case_id,
                from_status=from_status,
                to_status=to_status,
                allowed_statuses=self.next_statuses(from_status),
            )
        return rule


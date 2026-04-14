from __future__ import annotations

from dataclasses import dataclass

from ops_agent.models import CaseStatus


@dataclass(frozen=True, slots=True)
class TransitionRule:
    from_status: CaseStatus
    to_status: CaseStatus
    command_name: str
    reason_code: str


class InvalidStateTransitionError(ValueError):
    def __init__(self, *, case_id: str, from_status: CaseStatus, to_status: CaseStatus) -> None:
        super().__init__(f"Cannot transition case {case_id} from {from_status} to {to_status}.")
        self.case_id = case_id
        self.from_status = from_status
        self.to_status = to_status


class CaseStateMachine:
    def __init__(self, rules: list[TransitionRule]) -> None:
        self._rules = rules
        self._allowed: dict[CaseStatus, set[CaseStatus]] = {}
        for rule in rules:
            self._allowed.setdefault(rule.from_status, set()).add(rule.to_status)

    @classmethod
    def default(cls) -> "CaseStateMachine":
        return cls(
            rules=[
                TransitionRule(CaseStatus.RECEIVED, CaseStatus.STORED, "store_documents", "documents_stored"),
                TransitionRule(CaseStatus.STORED, CaseStatus.QUEUED, "queue_case", "case_queued"),
                TransitionRule(CaseStatus.QUEUED, CaseStatus.PROCESSING, "start_processing", "processing_started"),
                TransitionRule(CaseStatus.QUEUED, CaseStatus.REVIEW_REQUIRED, "queue_review", "review_task_created"),
                TransitionRule(CaseStatus.PROCESSING, CaseStatus.VALIDATED, "mark_validated", "validation_completed"),
                TransitionRule(CaseStatus.PROCESSING, CaseStatus.FAILED, "mark_failed", "processing_failed"),
                TransitionRule(CaseStatus.PROCESSING, CaseStatus.REVIEW_REQUIRED, "request_review", "review_required"),
                TransitionRule(CaseStatus.VALIDATED, CaseStatus.REVIEW_REQUIRED, "send_to_review", "review_required"),
                TransitionRule(CaseStatus.VALIDATED, CaseStatus.APPROVED, "approve_case", "case_approved"),
                TransitionRule(CaseStatus.VALIDATED, CaseStatus.REJECTED, "reject_case", "case_rejected"),
                TransitionRule(CaseStatus.REVIEW_REQUIRED, CaseStatus.IN_REVIEW, "claim_review", "review_started"),
                TransitionRule(CaseStatus.REVIEW_REQUIRED, CaseStatus.ESCALATED, "escalate_case", "case_escalated"),
                TransitionRule(CaseStatus.IN_REVIEW, CaseStatus.CORRECTED, "submit_corrections", "field_corrections_recorded"),
                TransitionRule(CaseStatus.IN_REVIEW, CaseStatus.ESCALATED, "escalate_case", "case_escalated"),
                TransitionRule(CaseStatus.IN_REVIEW, CaseStatus.APPROVED, "approve_case", "case_approved"),
                TransitionRule(CaseStatus.IN_REVIEW, CaseStatus.REJECTED, "reject_case", "case_rejected"),
                TransitionRule(CaseStatus.CORRECTED, CaseStatus.VALIDATED, "revalidate_case", "manual_revalidation_triggered"),
                TransitionRule(CaseStatus.CORRECTED, CaseStatus.REVIEW_REQUIRED, "return_to_review", "review_required"),
                TransitionRule(CaseStatus.ESCALATED, CaseStatus.IN_REVIEW, "claim_escalation", "review_started"),
                TransitionRule(CaseStatus.ESCALATED, CaseStatus.CLOSED, "close_case", "case_closed"),
                TransitionRule(CaseStatus.APPROVED, CaseStatus.CLOSED, "close_case", "case_closed"),
                TransitionRule(CaseStatus.REJECTED, CaseStatus.CLOSED, "close_case", "case_closed"),
                TransitionRule(CaseStatus.FAILED, CaseStatus.REVIEW_REQUIRED, "manual_recovery", "review_required"),
                TransitionRule(CaseStatus.FAILED, CaseStatus.CLOSED, "close_case", "case_closed"),
            ]
        )

    def can_transition(self, from_status: CaseStatus, to_status: CaseStatus) -> bool:
        return to_status in self._allowed.get(from_status, set())

    def assert_transition(self, *, case_id: str, from_status: CaseStatus, to_status: CaseStatus) -> None:
        if from_status == to_status:
            return
        if not self.can_transition(from_status, to_status):
            raise InvalidStateTransitionError(case_id=case_id, from_status=from_status, to_status=to_status)

    def next_statuses(self, from_status: CaseStatus) -> tuple[CaseStatus, ...]:
        return tuple(sorted(self._allowed.get(from_status, set())))

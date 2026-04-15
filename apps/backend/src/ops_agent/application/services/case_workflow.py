from __future__ import annotations

from ops_agent.domain.shared.enums import CaseStatus
from ops_agent.domain.workflow import (
    CaseStatusCarrier,
    CaseTransitionAuditHook,
    CaseTransitionContext,
    CaseTransitionRule,
    CaseWorkflowStateMachine,
    transition_case_status,
)


class CaseWorkflowService:
    """Applies explicit case lifecycle transitions with audit hooks."""

    def __init__(
        self,
        *,
        state_machine: CaseWorkflowStateMachine | None = None,
        audit_hooks: tuple[CaseTransitionAuditHook, ...] = (),
    ) -> None:
        self._state_machine = state_machine or CaseWorkflowStateMachine.default()
        self._audit_hooks = audit_hooks

    @property
    def state_machine(self) -> CaseWorkflowStateMachine:
        return self._state_machine

    def allowed_targets(self, from_status: CaseStatus) -> tuple[CaseStatus, ...]:
        return self._state_machine.next_statuses(from_status)

    def transition(
        self,
        *,
        case: CaseStatusCarrier,
        to_status: CaseStatus,
        context: CaseTransitionContext,
    ) -> CaseTransitionRule:
        return transition_case_status(
            case=case,
            to_status=to_status,
            context=context,
            state_machine=self._state_machine,
            audit_hooks=self._audit_hooks,
        )

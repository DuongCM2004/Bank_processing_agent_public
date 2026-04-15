from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from ops_agent.application.services.case_workflow import CaseWorkflowService
from ops_agent.domain.shared.enums import AuditActorType, AuditEventType, CaseStatus
from ops_agent.domain.workflow import (
    CaseTransitionAuditHook,
    CaseTransitionAuditRecord,
    CaseTransitionContext,
    CaseWorkflowStateMachine,
    InvalidCaseTransitionError,
)


@dataclass
class FakeCase:
    id: UUID
    status: CaseStatus
    status_changed_at: datetime
    updated_at: datetime
    updated_by: str | None = None


@dataclass
class RecordingAuditHook(CaseTransitionAuditHook):
    events: list[CaseTransitionAuditRecord] = field(default_factory=list)

    def record_transition(self, event: CaseTransitionAuditRecord) -> None:
        self.events.append(event)


def test_allowed_transitions_are_explicit() -> None:
    machine = CaseWorkflowStateMachine.default()

    assert machine.next_statuses(CaseStatus.CREATED) == (CaseStatus.DOCUMENTS_UPLOADED,)
    assert machine.next_statuses(CaseStatus.VALIDATION_COMPLETED) == (
        CaseStatus.MANUAL_REVIEW_REQUIRED,
        CaseStatus.DECISION_READY,
        CaseStatus.FAILED,
    )
    assert machine.next_statuses(CaseStatus.DECISION_READY) == (
        CaseStatus.MANUAL_REVIEW_REQUIRED,
        CaseStatus.APPROVED,
        CaseStatus.REJECTED,
    )


def test_invalid_transition_fails_clearly() -> None:
    machine = CaseWorkflowStateMachine.default()
    case_id = uuid4()

    with pytest.raises(InvalidCaseTransitionError) as exc_info:
        machine.validate_transition(
            case_id=case_id,
            from_status=CaseStatus.CREATED,
            to_status=CaseStatus.APPROVED,
        )

    message = str(exc_info.value)
    assert str(case_id) in message
    assert "'created'" in message
    assert "'approved'" in message
    assert "documents_uploaded" in message


def test_transition_updates_case_and_emits_audit_record() -> None:
    now = datetime.now(UTC)
    case = FakeCase(
        id=uuid4(),
        status=CaseStatus.QUEUED_FOR_PROCESSING,
        status_changed_at=now,
        updated_at=now,
    )
    audit_hook = RecordingAuditHook()
    service = CaseWorkflowService(audit_hooks=(audit_hook,))
    occurred_at = datetime(2026, 4, 15, 12, 0, tzinfo=UTC)

    rule = service.transition(
        case=case,
        to_status=CaseStatus.PROCESSING,
        context=CaseTransitionContext(
            actor_type=AuditActorType.SERVICE,
            actor_id="worker-processor",
            comment="Job picked up by processing worker.",
            metadata={"job_id": "job-123"},
            occurred_at=occurred_at,
        ),
    )

    assert rule.transition_name == "start_processing"
    assert case.status == CaseStatus.PROCESSING
    assert case.status_changed_at == occurred_at
    assert case.updated_by == "worker-processor"
    assert len(audit_hook.events) == 1
    audit_event = audit_hook.events[0]
    assert audit_event.case_id == case.id
    assert audit_event.from_status == CaseStatus.QUEUED_FOR_PROCESSING
    assert audit_event.to_status == CaseStatus.PROCESSING
    assert audit_event.reason_code == "processing_started"
    assert audit_event.actor_type == AuditActorType.SERVICE
    assert audit_event.event_type == AuditEventType.STATUS_CHANGED


def test_extraction_transition_uses_specific_audit_event_type() -> None:
    case = FakeCase(
        id=uuid4(),
        status=CaseStatus.PROCESSING,
        status_changed_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    audit_hook = RecordingAuditHook()
    service = CaseWorkflowService(audit_hooks=(audit_hook,))

    service.transition(
        case=case,
        to_status=CaseStatus.EXTRACTION_COMPLETED,
        context=CaseTransitionContext(actor_type=AuditActorType.SYSTEM, actor_id="pipeline"),
    )

    assert audit_hook.events[0].event_type == AuditEventType.EXTRACTION_COMPLETED
    assert audit_hook.events[0].reason_code == "extraction_completed"


def test_failed_cases_can_only_retry_via_explicit_transition() -> None:
    machine = CaseWorkflowStateMachine.default()

    assert machine.can_transition(CaseStatus.FAILED, CaseStatus.QUEUED_FOR_PROCESSING) is True
    assert machine.can_transition(CaseStatus.FAILED, CaseStatus.APPROVED) is False

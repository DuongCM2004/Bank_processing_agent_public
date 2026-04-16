from __future__ import annotations

import uuid

import pytest

from app.models.enums import CaseStatus
from app.workflows.case_state import CaseWorkflowStateMachine, InvalidCaseTransitionError


def test_default_workflow_allows_safe_happy_path_transition() -> None:
    machine = CaseWorkflowStateMachine.default()

    rule = machine.validate(
        case_id=uuid.uuid4(),
        from_status=CaseStatus.CREATED,
        to_status=CaseStatus.DOCUMENTS_UPLOADED,
    )

    assert rule.transition_name == "documents_registered"


def test_default_workflow_rejects_invalid_transition() -> None:
    machine = CaseWorkflowStateMachine.default()

    with pytest.raises(InvalidCaseTransitionError):
        machine.validate(
            case_id=uuid.uuid4(),
            from_status=CaseStatus.CREATED,
            to_status=CaseStatus.APPROVED,
        )


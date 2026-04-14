from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ops_agent.models import CaseStatus
from ops_agent.state_machine import CaseStateMachine, InvalidStateTransitionError


def test_state_machine_allows_review_claim_flow() -> None:
    machine = CaseStateMachine.default()

    assert machine.can_transition(CaseStatus.REVIEW_REQUIRED, CaseStatus.IN_REVIEW) is True
    assert machine.can_transition(CaseStatus.CORRECTED, CaseStatus.VALIDATED) is True


def test_state_machine_blocks_invalid_direct_close() -> None:
    machine = CaseStateMachine.default()

    with pytest.raises(InvalidStateTransitionError):
        machine.assert_transition(
            case_id="case_123",
            from_status=CaseStatus.REVIEW_REQUIRED,
            to_status=CaseStatus.CLOSED,
        )

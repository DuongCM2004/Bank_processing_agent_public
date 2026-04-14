from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from ops_agent.models import CaseStatus
from ops_agent.state_machine import CaseStateMachine, InvalidStateTransitionError


def example_test_invalid_transition_blocks_direct_close() -> None:
    machine = CaseStateMachine.default()

    with pytest.raises(InvalidStateTransitionError):
        machine.assert_transition(
            case_id="case_example",
            from_status=CaseStatus.REVIEW_REQUIRED,
            to_status=CaseStatus.CLOSED,
        )

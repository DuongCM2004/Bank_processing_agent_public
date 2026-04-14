from ops_agent.workflows.case_workflow import CASE_WORKFLOW_STEPS
from ops_agent.workflows.policy import MVP_STEP_POLICIES
from ops_agent.workflows.step_names import REVIEW_GATE_STEP


def test_all_workflow_steps_have_policies() -> None:
    step_names = {step.name for step in CASE_WORKFLOW_STEPS}
    assert step_names == set(MVP_STEP_POLICIES)


def test_review_gate_is_not_retryable_in_mvp() -> None:
    assert MVP_STEP_POLICIES[REVIEW_GATE_STEP].retry_policy.max_attempts == 1

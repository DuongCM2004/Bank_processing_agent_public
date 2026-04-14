from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ops_agent.observability import MVP_METRIC_NAMES, OperationalLogCategory, build_operational_log


ROOT = Path(__file__).resolve().parents[1]


def test_observability_spec_exists() -> None:
    spec_path = ROOT / "docs" / "observability-implementation-spec.md"
    assert spec_path.exists()


def test_operational_log_builder_captures_category_and_trace() -> None:
    event = build_operational_log(
        event_name="workflow_step_started",
        category=OperationalLogCategory.WORKFLOW,
        trace_id="trace_123",
        workflow_run_id="wf_123",
        workflow_step="ocr",
    )

    assert event.category == OperationalLogCategory.WORKFLOW
    assert event.trace_id == "trace_123"
    assert event.workflow_step == "ocr"


def test_mvp_metric_names_cover_workflow_and_audit_basics() -> None:
    assert "ops_agent_workflow_step_failed_total" in MVP_METRIC_NAMES
    assert "ops_agent_audit_write_failures_total" in MVP_METRIC_NAMES

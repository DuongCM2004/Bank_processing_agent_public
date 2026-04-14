from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StructuredLogEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_name: str
    trace_id: str
    case_id: str | None = None
    document_id: str | None = None
    review_task_id: str | None = None
    workflow_run_id: str | None = None
    severity: str = "INFO"
    recorded_at_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))
    details: dict[str, Any] = Field(default_factory=dict)


def build_log_event(
    *,
    event_name: str,
    trace_id: str,
    severity: str = "INFO",
    case_id: str | None = None,
    document_id: str | None = None,
    review_task_id: str | None = None,
    workflow_run_id: str | None = None,
    **details: Any,
) -> StructuredLogEvent:
    return StructuredLogEvent(
        event_name=event_name,
        trace_id=trace_id,
        severity=severity,
        case_id=case_id,
        document_id=document_id,
        review_task_id=review_task_id,
        workflow_run_id=workflow_run_id,
        details=details,
    )


def build_agent_audit_details(
    *,
    capability: str,
    prompt_id: str,
    prompt_version: str,
    schema_name: str,
    schema_file: str,
    model_name: str,
    status: str,
    escalation_target: str,
    reason_codes: list[str],
    evidence_refs: list[dict[str, Any]],
    model_version: str | None = None,
    confidence_score: float | None = None,
    reasoning_summary: str | None = None,
    raw_output_artifact_id: str | None = None,
) -> dict[str, Any]:
    return {
        "capability": capability,
        "prompt_id": prompt_id,
        "prompt_version": prompt_version,
        "schema_name": schema_name,
        "schema_file": schema_file,
        "model_name": model_name,
        "model_version": model_version,
        "status": status,
        "escalation_target": escalation_target,
        "confidence_score": confidence_score,
        "reason_codes": reason_codes,
        "evidence_refs": evidence_refs,
        # Persist only bounded reviewer-safe summaries, not raw chain-of-thought.
        "reasoning_summary": reasoning_summary,
        "raw_output_artifact_id": raw_output_artifact_id,
    }

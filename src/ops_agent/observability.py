from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def telemetry_timestamp() -> datetime:
    return datetime.now(UTC)


class OperationalLogCategory(StrEnum):
    API_REQUEST = "api_request"
    AUTH = "auth"
    CASE_LIFECYCLE = "case_lifecycle"
    DOCUMENT_IO = "document_io"
    WORKFLOW = "workflow"
    AGENT_RUNTIME = "agent_runtime"
    REVIEW = "review"
    QUEUE = "queue"
    INTEGRATION = "integration"
    SECURITY = "security"
    AUDIT_PIPELINE = "audit_pipeline"


class MetricKind(StrEnum):
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"


class TelemetryModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OperationalLogRecord(TelemetryModel):
    event_name: str
    category: OperationalLogCategory
    trace_id: str
    severity: str = "INFO"
    message: str | None = None
    case_id: str | None = None
    document_id: str | None = None
    review_task_id: str | None = None
    workflow_run_id: str | None = None
    workflow_step: str | None = None
    queue_name: str | None = None
    actor_id: str | None = None
    actor_type: str | None = None
    correlation_id: str | None = None
    integration_name: str | None = None
    provider_request_id: str | None = None
    attempt_no: int | None = Field(default=None, ge=1)
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    reason_codes: list[str] = Field(default_factory=list)
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    recorded_at_utc: datetime = Field(default_factory=telemetry_timestamp)
    details: dict[str, Any] = Field(default_factory=dict)


class MetricPoint(TelemetryModel):
    metric_name: str
    kind: MetricKind
    value: float
    unit: str | None = None
    trace_id: str | None = None
    case_id: str | None = None
    workflow_run_id: str | None = None
    workflow_step: str | None = None
    queue_name: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    recorded_at_utc: datetime = Field(default_factory=telemetry_timestamp)


def build_operational_log(
    *,
    event_name: str,
    category: OperationalLogCategory,
    trace_id: str,
    severity: str = "INFO",
    message: str | None = None,
    case_id: str | None = None,
    document_id: str | None = None,
    review_task_id: str | None = None,
    workflow_run_id: str | None = None,
    workflow_step: str | None = None,
    queue_name: str | None = None,
    actor_id: str | None = None,
    actor_type: str | None = None,
    correlation_id: str | None = None,
    integration_name: str | None = None,
    provider_request_id: str | None = None,
    attempt_no: int | None = None,
    confidence_score: float | None = None,
    reason_codes: list[str] | None = None,
    evidence_refs: list[dict[str, Any]] | None = None,
    **details: Any,
) -> OperationalLogRecord:
    return OperationalLogRecord(
        event_name=event_name,
        category=category,
        trace_id=trace_id,
        severity=severity,
        message=message,
        case_id=case_id,
        document_id=document_id,
        review_task_id=review_task_id,
        workflow_run_id=workflow_run_id,
        workflow_step=workflow_step,
        queue_name=queue_name,
        actor_id=actor_id,
        actor_type=actor_type,
        correlation_id=correlation_id,
        integration_name=integration_name,
        provider_request_id=provider_request_id,
        attempt_no=attempt_no,
        confidence_score=confidence_score,
        reason_codes=reason_codes or [],
        evidence_refs=evidence_refs or [],
        details=details,
    )


def build_metric_point(
    *,
    metric_name: str,
    kind: MetricKind,
    value: float,
    unit: str | None = None,
    trace_id: str | None = None,
    case_id: str | None = None,
    workflow_run_id: str | None = None,
    workflow_step: str | None = None,
    queue_name: str | None = None,
    labels: dict[str, str] | None = None,
) -> MetricPoint:
    return MetricPoint(
        metric_name=metric_name,
        kind=kind,
        value=value,
        unit=unit,
        trace_id=trace_id,
        case_id=case_id,
        workflow_run_id=workflow_run_id,
        workflow_step=workflow_step,
        queue_name=queue_name,
        labels=labels or {},
    )


MVP_METRIC_NAMES: tuple[str, ...] = (
    "ops_agent_cases_created_total",
    "ops_agent_case_state_transitions_total",
    "ops_agent_case_processing_duration_seconds",
    "ops_agent_workflow_step_started_total",
    "ops_agent_workflow_step_completed_total",
    "ops_agent_workflow_step_failed_total",
    "ops_agent_workflow_step_retry_total",
    "ops_agent_workflow_step_duration_seconds",
    "ops_agent_review_tasks_open",
    "ops_agent_review_task_age_seconds",
    "ops_agent_review_actions_total",
    "ops_agent_queue_depth",
    "ops_agent_queue_oldest_age_seconds",
    "ops_agent_integration_requests_total",
    "ops_agent_integration_failures_total",
    "ops_agent_integration_latency_seconds",
    "ops_agent_agent_low_confidence_total",
    "ops_agent_agent_schema_validation_failures_total",
    "ops_agent_agent_quality_score",
    "ops_agent_audit_write_failures_total",
)

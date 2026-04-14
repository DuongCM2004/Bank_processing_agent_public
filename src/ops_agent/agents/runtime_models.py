from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ops_agent.workflow_contracts import VersionRefs


def runtime_timestamp() -> datetime:
    return datetime.now(UTC)


AgentOutcomeStatus = Literal["completed", "needs_review", "insufficient_evidence", "error"]


class RuntimeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AgentInvocationContext(RuntimeModel):
    trace_id: str
    case_id: str
    document_id: str | None = None
    workflow_run_id: str
    step_name: str
    initiated_by: str
    attempt_no: int = Field(default=1, ge=1)
    schema_version: str
    timestamp_utc: datetime = Field(default_factory=runtime_timestamp)
    version_refs: VersionRefs


class AgentHandoff(RuntimeModel):
    from_agent: str
    to_agent: str
    handoff_reason: str
    input_artifact_ids: list[str] = Field(default_factory=list)
    inherited_reason_codes: list[str] = Field(default_factory=list)
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)


class AgentInvocationRequest(RuntimeModel):
    capability: str
    prompt_id: str
    prompt_version: str
    schema_name: str
    schema_file: str
    model_name: str
    temperature: float = Field(default=0.0, ge=0.0, le=0.3)
    role_boundary: str
    context: AgentInvocationContext
    allowed_statuses: list[AgentOutcomeStatus]
    allowed_escalation_targets: list[str]
    evidence_bundle: dict[str, Any] = Field(default_factory=dict)
    input_payload: dict[str, Any] = Field(default_factory=dict)
    handoff: AgentHandoff | None = None
    idempotency_key: str


class AgentValidatedResult(RuntimeModel):
    capability: str
    prompt_id: str
    prompt_version: str
    schema_name: str
    schema_file: str
    model_name: str
    model_version: str | None = None
    status: AgentOutcomeStatus
    escalation_target: str = "none"
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    reason_codes: list[str] = Field(default_factory=list)
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    output_payload: dict[str, Any] = Field(default_factory=dict)
    reasoning_summary: str | None = None
    raw_output_artifact_id: str | None = None
    created_at_utc: datetime = Field(default_factory=runtime_timestamp)


class AgentFailure(RuntimeModel):
    capability: str
    prompt_id: str
    prompt_version: str
    schema_file: str
    error_code: str
    retryable: bool
    safe_message: str
    provider_status_code: int | None = None
    provider_request_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)

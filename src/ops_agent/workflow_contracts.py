from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ContractModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")


def contract_timestamp() -> datetime:
    return datetime.now(UTC)


class VersionRefs(ContractModel):
    workflow_definition_version: str | None = None
    schema_version: str
    rule_pack_version: str | None = None
    ocr_model_version: str | None = None
    classifier_model_version: str | None = None
    prompt_version: str | None = None
    preprocess_profile_version: str | None = None


class ArtifactRefs(ContractModel):
    source_document_ref: str | None = None
    source_document_version_id: str | None = None
    input_artifact_id: str | None = None
    output_artifact_id: str | None = None


class WorkflowStartCommand(ContractModel):
    trace_id: str
    case_id: str
    workflow_type: str
    document_ids: list[str] = Field(default_factory=list)
    initiated_by: str
    timestamp_utc: datetime = Field(default_factory=contract_timestamp)
    version_refs: VersionRefs


class ReviewCompletionSignal(ContractModel):
    trace_id: str
    case_id: str
    review_task_id: str
    triggered_by: str
    timestamp_utc: datetime = Field(default_factory=contract_timestamp)
    outcome: str
    reason_codes: list[str] = Field(default_factory=list)


class ProcessingJobCommand(ContractModel):
    trace_id: str
    case_id: str
    document_id: str
    workflow_run_id: str
    step_name: str
    attempt_no: int = Field(ge=1, default=1)
    producer_service: str
    timestamp_utc: datetime = Field(default_factory=contract_timestamp)
    artifact_refs: ArtifactRefs
    version_refs: VersionRefs
    payload: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunStatusResponse(ContractModel):
    workflow_run_id: str
    case_id: str
    status: str
    active_step: str | None = None
    pending_review_task_id: str | None = None
    started_at_utc: datetime
    updated_at_utc: datetime
    retryable_failure_count: int = 0
    latest_error_code: str | None = None

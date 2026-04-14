from __future__ import annotations

from dataclasses import dataclass

from ops_agent.models import CaseStatus
from ops_agent.workflows.step_names import (
    CLASSIFICATION_STEP,
    DECISION_STEP,
    EXTRACTION_STEP,
    INGESTION_STEP,
    LAYOUT_STEP,
    OCR_STEP,
    REVIEW_GATE_STEP,
    VALIDATION_STEP,
)


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int
    initial_delay_seconds: int
    backoff_multiplier: float
    max_delay_seconds: int
    non_retryable_error_codes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TimeoutPolicy:
    start_to_close_seconds: int
    schedule_to_close_seconds: int
    heartbeat_timeout_seconds: int | None = None


@dataclass(frozen=True, slots=True)
class ReviewRoutingPolicy:
    low_confidence_threshold: float | None = None
    escalate_on_reason_codes: tuple[str, ...] = ()
    default_review_queue: str = "ops_review_general"
    escalation_queue: str = "ops_review_supervisor"


@dataclass(frozen=True, slots=True)
class StepExecutionPolicy:
    step_name: str
    stage_name: str
    queue_name: str
    retry_policy: RetryPolicy
    timeout_policy: TimeoutPolicy
    review_routing: ReviewRoutingPolicy
    idempotency_scope: str
    success_transition: tuple[CaseStatus, CaseStatus] | None = None
    failure_transition: tuple[CaseStatus, CaseStatus] | None = None
    emits_audit_actions: tuple[str, ...] = ()


MVP_STEP_POLICIES: dict[str, StepExecutionPolicy] = {
    INGESTION_STEP: StepExecutionPolicy(
        step_name=INGESTION_STEP,
        stage_name="intake_registration",
        queue_name="ops_agent_ingestion",
        retry_policy=RetryPolicy(
            max_attempts=1,
            initial_delay_seconds=0,
            backoff_multiplier=1.0,
            max_delay_seconds=0,
        ),
        timeout_policy=TimeoutPolicy(
            start_to_close_seconds=30,
            schedule_to_close_seconds=120,
        ),
        review_routing=ReviewRoutingPolicy(),
        idempotency_scope="case_id",
        success_transition=(CaseStatus.RECEIVED, CaseStatus.STORED),
        emits_audit_actions=("case_stored",),
    ),
    OCR_STEP: StepExecutionPolicy(
        step_name=OCR_STEP,
        stage_name="ocr_capture",
        queue_name="ops_agent_ocr",
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=30,
            backoff_multiplier=2.0,
            max_delay_seconds=300,
            non_retryable_error_codes=("unsupported_file_type", "corrupt_document"),
        ),
        timeout_policy=TimeoutPolicy(
            start_to_close_seconds=300,
            schedule_to_close_seconds=1200,
            heartbeat_timeout_seconds=60,
        ),
        review_routing=ReviewRoutingPolicy(
            low_confidence_threshold=0.85,
            escalate_on_reason_codes=("possible_document_tampering",),
        ),
        idempotency_scope="workflow_run_id:document_id:step_name",
        emits_audit_actions=("ocr_requested", "ocr_completed"),
    ),
    LAYOUT_STEP: StepExecutionPolicy(
        step_name=LAYOUT_STEP,
        stage_name="layout_analysis",
        queue_name="ops_agent_layout",
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=30,
            backoff_multiplier=2.0,
            max_delay_seconds=300,
        ),
        timeout_policy=TimeoutPolicy(
            start_to_close_seconds=180,
            schedule_to_close_seconds=900,
            heartbeat_timeout_seconds=60,
        ),
        review_routing=ReviewRoutingPolicy(
            low_confidence_threshold=0.80,
        ),
        idempotency_scope="workflow_run_id:document_id:step_name",
        emits_audit_actions=("layout_analysis_completed",),
    ),
    CLASSIFICATION_STEP: StepExecutionPolicy(
        step_name=CLASSIFICATION_STEP,
        stage_name="document_classification",
        queue_name="ops_agent_classification",
        retry_policy=RetryPolicy(
            max_attempts=2,
            initial_delay_seconds=30,
            backoff_multiplier=2.0,
            max_delay_seconds=180,
        ),
        timeout_policy=TimeoutPolicy(
            start_to_close_seconds=120,
            schedule_to_close_seconds=600,
        ),
        review_routing=ReviewRoutingPolicy(
            low_confidence_threshold=0.80,
            escalate_on_reason_codes=("document_type_conflict",),
        ),
        idempotency_scope="workflow_run_id:document_id:step_name",
        emits_audit_actions=("classification_completed",),
    ),
    EXTRACTION_STEP: StepExecutionPolicy(
        step_name=EXTRACTION_STEP,
        stage_name="field_extraction",
        queue_name="ops_agent_extraction",
        retry_policy=RetryPolicy(
            max_attempts=2,
            initial_delay_seconds=30,
            backoff_multiplier=2.0,
            max_delay_seconds=180,
        ),
        timeout_policy=TimeoutPolicy(
            start_to_close_seconds=180,
            schedule_to_close_seconds=900,
            heartbeat_timeout_seconds=60,
        ),
        review_routing=ReviewRoutingPolicy(
            low_confidence_threshold=0.85,
            escalate_on_reason_codes=("required_field_missing", "conflicting_field_values"),
        ),
        idempotency_scope="workflow_run_id:document_id:step_name",
        emits_audit_actions=("extraction_completed",),
    ),
    VALIDATION_STEP: StepExecutionPolicy(
        step_name=VALIDATION_STEP,
        stage_name="rules_validation",
        queue_name="ops_agent_validation",
        retry_policy=RetryPolicy(
            max_attempts=2,
            initial_delay_seconds=15,
            backoff_multiplier=2.0,
            max_delay_seconds=120,
        ),
        timeout_policy=TimeoutPolicy(
            start_to_close_seconds=120,
            schedule_to_close_seconds=600,
        ),
        review_routing=ReviewRoutingPolicy(
            escalate_on_reason_codes=("critical_validation_failure", "policy_violation"),
        ),
        idempotency_scope="workflow_run_id:case_id:step_name",
        success_transition=(CaseStatus.PROCESSING, CaseStatus.VALIDATED),
        emits_audit_actions=("validation_completed",),
    ),
    DECISION_STEP: StepExecutionPolicy(
        step_name=DECISION_STEP,
        stage_name="routing_decision",
        queue_name="ops_agent_decision",
        retry_policy=RetryPolicy(
            max_attempts=2,
            initial_delay_seconds=15,
            backoff_multiplier=2.0,
            max_delay_seconds=120,
        ),
        timeout_policy=TimeoutPolicy(
            start_to_close_seconds=60,
            schedule_to_close_seconds=300,
        ),
        review_routing=ReviewRoutingPolicy(
            escalate_on_reason_codes=(
                "fraud_high_risk",
                "aml_watchlist_possible_match",
                "sanctions_possible_match",
            ),
        ),
        idempotency_scope="workflow_run_id:case_id:step_name",
        emits_audit_actions=("decision_recommended",),
    ),
    REVIEW_GATE_STEP: StepExecutionPolicy(
        step_name=REVIEW_GATE_STEP,
        stage_name="manual_review_gate",
        queue_name="ops_agent_review_gate",
        retry_policy=RetryPolicy(
            max_attempts=1,
            initial_delay_seconds=0,
            backoff_multiplier=1.0,
            max_delay_seconds=0,
        ),
        timeout_policy=TimeoutPolicy(
            start_to_close_seconds=30,
            schedule_to_close_seconds=120,
        ),
        review_routing=ReviewRoutingPolicy(
            low_confidence_threshold=0.90,
            escalate_on_reason_codes=(
                "fraud_high_risk",
                "aml_watchlist_possible_match",
                "sanctions_possible_match",
                "critical_validation_failure",
            ),
        ),
        idempotency_scope="workflow_run_id:case_id:step_name",
        success_transition=(CaseStatus.PROCESSING, CaseStatus.REVIEW_REQUIRED),
        failure_transition=(CaseStatus.PROCESSING, CaseStatus.FAILED),
        emits_audit_actions=("review_gate_evaluated", "review_task_created"),
    ),
}


def get_step_policy(step_name: str) -> StepExecutionPolicy:
    return MVP_STEP_POLICIES[step_name]

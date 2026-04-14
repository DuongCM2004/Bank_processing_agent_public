from __future__ import annotations

from dataclasses import dataclass

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
class WorkflowStepSpec:
    name: str
    retryable: bool
    requires_document_context: bool = True


CASE_WORKFLOW_STEPS: tuple[WorkflowStepSpec, ...] = (
    WorkflowStepSpec(name=INGESTION_STEP, retryable=False),
    WorkflowStepSpec(name=OCR_STEP, retryable=True),
    WorkflowStepSpec(name=LAYOUT_STEP, retryable=True),
    WorkflowStepSpec(name=CLASSIFICATION_STEP, retryable=True),
    WorkflowStepSpec(name=EXTRACTION_STEP, retryable=True),
    WorkflowStepSpec(name=VALIDATION_STEP, retryable=True),
    WorkflowStepSpec(name=DECISION_STEP, retryable=True, requires_document_context=False),
    WorkflowStepSpec(name=REVIEW_GATE_STEP, retryable=False, requires_document_context=False),
)


class CaseProcessingWorkflow:
    """Starter workflow skeleton.

    Production implementation should move this into Temporal decorators and
    activities. The scaffold remains explicit about step ordering and retry
    intent so backend and platform teams can evolve it safely.
    """

    steps = CASE_WORKFLOW_STEPS

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PromptDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt_id: str
    owner: str
    role_boundary: str
    allowed_statuses: list[str]
    escalation_targets: list[str]
    requires_evidence: bool = True
    schema_name: str
    schema_file: str
    prompt_version: str
    reasoning_summary_max_chars: int = Field(default=400, ge=120, le=2000)
    change_control_required: bool = True


PROMPT_REGISTRY: dict[str, PromptDefinition] = {
    "ocr_reconcile": PromptDefinition(
        prompt_id="ocr_reconcile_v1",
        owner="ml-platform",
        role_boundary="Reconcile OCR span candidates only. Never infer business meaning or missing characters.",
        allowed_statuses=["completed", "needs_review", "insufficient_evidence", "error"],
        escalation_targets=["none", "ops_review"],
        schema_name="ocr-reconcile-response",
        schema_file="ocr-result.json",
        prompt_version="2026-04-14",
    ),
    "document_classify_tiebreak": PromptDefinition(
        prompt_id="document_classify_tiebreak_v1",
        owner="ml-platform",
        role_boundary="Choose only among allowed document labels. Never invent a new label or route the case.",
        allowed_statuses=["completed", "needs_review", "insufficient_evidence", "error"],
        escalation_targets=["none", "ops_review"],
        schema_name="classification-output",
        schema_file="classification-result.json",
        prompt_version="2026-04-14",
    ),
    "field_extract_reconcile": PromptDefinition(
        prompt_id="field_extract_reconcile_v1",
        owner="ml-platform",
        role_boundary="Resolve extraction ambiguity for one document schema. Never approve, reject, or fabricate values.",
        allowed_statuses=["completed", "needs_review", "insufficient_evidence", "error"],
        escalation_targets=["none", "ops_review", "manual_resubmission"],
        schema_name="extraction-output",
        schema_file="extraction-result.json",
        prompt_version="2026-04-14",
    ),
    "compliance_review_summary": PromptDefinition(
        prompt_id="compliance_review_summary_v1",
        owner="risk-controls",
        role_boundary="Summarize control results for a human specialist. Never clear sanctions, AML, or fraud concerns.",
        allowed_statuses=["completed", "needs_review", "insufficient_evidence", "error"],
        escalation_targets=["none", "compliance_review", "fraud_review"],
        schema_name="compliance-summary",
        schema_file="risk-compliance-result.json",
        prompt_version="2026-04-14",
    ),
    "review_copilot": PromptDefinition(
        prompt_id="review_copilot_v1",
        owner="ops-platform",
        role_boundary="Assist the reviewer with evidence-linked summaries only. Reviewer remains decision-maker.",
        allowed_statuses=["completed", "needs_review", "insufficient_evidence", "error"],
        escalation_targets=["none", "ops_review", "compliance_review", "fraud_review"],
        schema_name="review-copilot-response",
        schema_file="manual-review-action.json",
        prompt_version="2026-04-14",
    ),
}


def get_prompt_definition(capability: str) -> PromptDefinition:
    return PROMPT_REGISTRY[capability]

from __future__ import annotations

from typing import Any


def build_document_create(
    *,
    filename: str = "document.pdf",
    mime_type: str = "application/pdf",
    source_channel: str = "ops_upload",
    retention_class: str = "bank_ops_default",
) -> dict[str, Any]:
    return {
        "filename": filename,
        "mime_type": mime_type,
        "source_channel": source_channel,
        "retention_class": retention_class,
    }


def build_case_create_request(
    *,
    workflow_type: str = "kyc_onboarding",
    priority: str = "normal",
    review_required: bool = True,
    customer_reference: str | None = "cust_fixture_001",
    documents: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "workflow_type": workflow_type,
        "priority": priority,
        "review_required": review_required,
        "customer_reference": customer_reference,
        "documents": documents or [build_document_create()],
    }


def build_field_correction_request(
    *,
    reviewer_id: str = "reviewer_fixture",
    field_name: str = "account_number",
    new_value: str = "1234567890",
    reason_code: str = "reviewer_confirmed",
    document_id: str = "doc_fixture",
) -> dict[str, Any]:
    return {
        "reviewer_id": reviewer_id,
        "corrections": [
            {
                "field_name": field_name,
                "new_value": new_value,
                "reason_code": reason_code,
                "evidence_refs": [
                    {
                        "document_id": document_id,
                        "page_number": 1,
                        "text_span": f"{field_name} {new_value}",
                    }
                ],
            }
        ],
    }

from __future__ import annotations

from typing import Any


class FakeOCRProvider:
    def __init__(self, *, submission_id: str = "ocr_job_fixture") -> None:
        self.submission_id = submission_id

    def submit(self, *, case_id: str, document_id: str, object_key: str) -> str:
        return self.submission_id


class FakeDocumentClassifierProvider:
    def __init__(
        self,
        *,
        label: str = "bank_statement",
        confidence_score: float = 0.97,
        status: str = "completed",
    ) -> None:
        self.label = label
        self.confidence_score = confidence_score
        self.status = status

    def classify(self, *, case_id: str, document_id: str, artifact_id: str) -> dict[str, Any]:
        return {
            "status": self.status,
            "document_type": self.label,
            "confidence_score": self.confidence_score,
            "reason_codes": [],
            "evidence_refs": [{"document_id": document_id, "page_number": 1}],
        }


class FakeFieldExtractorProvider:
    def __init__(
        self,
        *,
        status: str = "completed",
        confidence_score: float = 0.96,
        field_name: str = "account_number",
        field_value: str = "1234567890",
    ) -> None:
        self.status = status
        self.confidence_score = confidence_score
        self.field_name = field_name
        self.field_value = field_value

    def extract(self, *, case_id: str, document_id: str, schema_name: str, artifact_id: str) -> dict[str, Any]:
        return {
            "status": self.status,
            "confidence_score": self.confidence_score,
            "reason_codes": [],
            "evidence_refs": [{"document_id": document_id, "page_number": 1}],
            "fields": [
                {
                    "field_name": self.field_name,
                    "value": self.field_value,
                    "confidence_score": self.confidence_score,
                    "evidence_refs": [{"document_id": document_id, "page_number": 1}],
                }
            ],
        }


class FakeValidationProvider:
    def __init__(self, *, result: str = "pass", reason_code: str = "all_checks_passed") -> None:
        self.result = result
        self.reason_code = reason_code

    def validate(self, *, case_id: str, document_id: str | None = None) -> dict[str, Any]:
        return {
            "status": "completed",
            "overall_result": self.result,
            "reason_codes": [self.reason_code],
            "findings": [],
        }


class FakeDecisionProvider:
    def __init__(self, *, recommended_route: str = "review_required", reason_code: str = "manual_review_default") -> None:
        self.recommended_route = recommended_route
        self.reason_code = reason_code

    def decide(self, *, case_id: str) -> dict[str, Any]:
        return {
            "status": "completed",
            "recommended_route": self.recommended_route,
            "reason_codes": [self.reason_code],
        }

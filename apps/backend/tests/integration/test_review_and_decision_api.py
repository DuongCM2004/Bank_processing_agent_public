from __future__ import annotations

from uuid import uuid4

import pytest

from ops_agent.domain.shared.enums import CaseStatus, DocumentStatus, FindingSeverity, FindingStatus, RiskLevel
from ops_agent.infrastructure.db.models import ComplianceFinding, RiskFinding, ValidationFinding
from tests.fixtures.builders import seed_review_case


pytestmark = pytest.mark.integration


def _seed_findings(db_session, *, case_id, document_id, extraction_result_id) -> tuple[ValidationFinding, RiskFinding, ComplianceFinding]:
    validation_finding = ValidationFinding(
        case_id=case_id,
        document_id=document_id,
        extraction_result_id=extraction_result_id,
        rule_code="required_document_number",
        field_name="document_number",
        message="Document number format must be reviewed.",
        severity=FindingSeverity.ERROR,
        status=FindingStatus.OPEN,
        evidence_refs=[{"document_id": str(document_id), "page_number": 1}],
    )
    risk_finding = RiskFinding(
        case_id=case_id,
        document_id=document_id,
        extraction_result_id=extraction_result_id,
        risk_code="name_screening_review",
        message="Customer requires enhanced due diligence review.",
        risk_level=RiskLevel.HIGH,
        status=FindingStatus.OPEN,
        evidence_refs=[{"document_id": str(document_id), "page_number": 1}],
    )
    compliance_finding = ComplianceFinding(
        case_id=case_id,
        document_id=document_id,
        extraction_result_id=extraction_result_id,
        policy_code="kyc-001",
        message="Proof-of-identity evidence requires secondary validation.",
        severity=FindingSeverity.WARNING,
        status=FindingStatus.OPEN,
        evidence_refs=[{"document_id": str(document_id), "page_number": 1}],
    )
    db_session.add_all([validation_finding, risk_finding, compliance_finding])
    db_session.commit()
    return validation_finding, risk_finding, compliance_finding


def test_manual_review_submission_records_before_after_correction(client, db_session) -> None:
    reviewer_id = uuid4()
    case, document, extraction_result = seed_review_case(
        db_session,
        case_status=CaseStatus.MANUAL_REVIEW_REQUIRED,
        document_status=DocumentStatus.REVIEW_REQUIRED,
        extracted_payload={"document_number": "OLD123", "full_name": "Alice Example"},
    )

    response = client.post(
        f"/api/v1/cases/{case.id}/manual-review/corrections",
        json={
            "performed_by_user_id": str(reviewer_id),
            "document_id": str(document.id),
            "comment": "Corrected OCR digit transcription.",
            "corrections": [
                {
                    "extraction_result_id": str(extraction_result.id),
                    "field_name": "document_number",
                    "before_value": "OLD123",
                    "after_value": "NEW123",
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["action"]["action_type"] == "correct_data"
    assert payload["corrections"][0]["before_value"] == "OLD123"
    assert payload["corrections"][0]["after_value"] == "NEW123"


def test_decision_submission_links_findings_and_updates_case_status(client, db_session) -> None:
    reviewer_id = uuid4()
    case, document, extraction_result = seed_review_case(
        db_session,
        case_status=CaseStatus.DECISION_READY,
        document_status=DocumentStatus.EXTRACTION_COMPLETED,
        extracted_payload={"document_number": "A1234567", "full_name": "Alice Example"},
    )
    validation_finding, risk_finding, compliance_finding = _seed_findings(
        db_session,
        case_id=case.id,
        document_id=document.id,
        extraction_result_id=extraction_result.id,
    )

    response = client.post(
        f"/api/v1/cases/{case.id}/decisions",
        json={
            "decided_by_user_id": str(reviewer_id),
            "decision_type": "reviewer_decision",
            "outcome": "review_required",
            "reason_code": "findings_require_manual_review",
            "rationale": "Conflicting indicators require a human decision.",
            "linked_findings": [
                {"finding_type": "validation", "finding_id": str(validation_finding.id)},
                {"finding_type": "risk", "finding_id": str(risk_finding.id)},
                {"finding_type": "compliance", "finding_id": str(compliance_finding.id)},
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["case_status"] == "manual_review_required"
    assert payload["decision"]["outcome"] == "review_required"
    assert len(payload["decision"]["linked_findings"]) == 3

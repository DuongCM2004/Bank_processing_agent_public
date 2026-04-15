from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID
from uuid import uuid4

from ops_agent.domain.shared.enums import (
    AuditEventType,
    CaseStatus,
    DecisionOutcome,
    DocumentStatus,
    FindingSeverity,
    FindingStatus,
    ProcessingStatus,
    RiskLevel,
)
from ops_agent.infrastructure.db.models import (
    AuditEvent,
    Case,
    ComplianceFinding,
    Decision,
    Document,
    ExtractionResult,
    RiskFinding,
    ValidationFinding,
)


def _seed_decision_case(db_session, *, case_status: CaseStatus) -> tuple[Case, Document, ExtractionResult]:
    now = datetime.now(UTC)
    case = Case(
        case_reference=f"CASE-DECISION-{uuid4().hex[:8]}",
        case_type="kyc_onboarding",
        status=case_status,
        status_changed_at=now,
        current_queue="document_ops",
        source_channel="manual_upload",
    )
    db_session.add(case)
    db_session.flush()

    document = Document(
        case_id=case.id,
        filename="passport.pdf",
        document_type="passport",
        mime_type="application/pdf",
        storage_key=f"cases/{case.id}/documents/passport.pdf",
        sha256_digest="c" * 64,
        file_size_bytes=4096,
        uploaded_at=now,
        status=DocumentStatus.EXTRACTION_COMPLETED,
        status_changed_at=now,
        source_channel="manual_upload",
    )
    db_session.add(document)
    db_session.flush()

    extraction_result = ExtractionResult(
        document_id=document.id,
        status=ProcessingStatus.COMPLETED,
        schema_name="passport_mvp",
        extracted_payload={"document_number": "A1234567", "full_name": "Alice Example"},
        confidence_score=0.94,
        evidence_refs=[{"document_id": str(document.id), "page_number": 1, "metadata": {"field_name": "document_number"}}],
        provider_name="placeholder_extraction",
        processed_at=now,
    )
    db_session.add(extraction_result)
    db_session.commit()
    return case, document, extraction_result


def _seed_findings(db_session, *, case: Case, document: Document, extraction_result: ExtractionResult) -> tuple[ValidationFinding, RiskFinding, ComplianceFinding]:
    validation_finding = ValidationFinding(
        case_id=case.id,
        document_id=document.id,
        extraction_result_id=extraction_result.id,
        rule_code="required_document_number",
        field_name="document_number",
        message="Document number format must be reviewed.",
        severity=FindingSeverity.ERROR,
        status=FindingStatus.OPEN,
        evidence_refs=[{"document_id": str(document.id), "page_number": 1}],
    )
    risk_finding = RiskFinding(
        case_id=case.id,
        document_id=document.id,
        extraction_result_id=extraction_result.id,
        risk_code="name_screening_review",
        message="Customer requires enhanced due diligence review.",
        risk_level=RiskLevel.HIGH,
        status=FindingStatus.OPEN,
        evidence_refs=[{"document_id": str(document.id), "page_number": 1}],
    )
    compliance_finding = ComplianceFinding(
        case_id=case.id,
        document_id=document.id,
        extraction_result_id=extraction_result.id,
        policy_code="kyc-001",
        message="Proof-of-identity evidence requires secondary validation.",
        severity=FindingSeverity.WARNING,
        status=FindingStatus.OPEN,
        evidence_refs=[{"document_id": str(document.id), "page_number": 1}],
    )
    db_session.add_all([validation_finding, risk_finding, compliance_finding])
    db_session.commit()
    return validation_finding, risk_finding, compliance_finding


def test_create_decision_links_findings_and_emits_audit_event(client, db_session) -> None:
    reviewer_id = uuid4()
    case, document, extraction_result = _seed_decision_case(db_session, case_status=CaseStatus.DECISION_READY)
    validation_finding, risk_finding, compliance_finding = _seed_findings(
        db_session,
        case=case,
        document=document,
        extraction_result=extraction_result,
    )

    response = client.post(
        f"/api/v1/cases/{case.id}/decisions",
        json={
            "decided_by_user_id": str(reviewer_id),
            "decision_type": "reviewer_decision",
            "outcome": "review_required",
            "reason_code": "findings_require_manual_review",
            "rationale": "Conflicting indicators require a human decision.",
            "confidence_score": 0.72,
            "evidence_refs": [{"document_id": str(document.id), "page_number": 1}],
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
    assert payload["decision"]["linked_findings"] == [
        {"finding_type": "validation", "finding_id": str(validation_finding.id)},
        {"finding_type": "risk", "finding_id": str(risk_finding.id)},
        {"finding_type": "compliance", "finding_id": str(compliance_finding.id)},
    ]

    decision = db_session.get(Decision, UUID(payload["decision"]["id"]))
    refreshed_case = db_session.get(Case, case.id)
    assert decision is not None
    assert refreshed_case is not None and refreshed_case.status == CaseStatus.MANUAL_REVIEW_REQUIRED
    assert decision.outcome == DecisionOutcome.REVIEW_REQUIRED
    assert decision.linked_findings == [
        {"finding_type": "validation", "finding_id": str(validation_finding.id)},
        {"finding_type": "risk", "finding_id": str(risk_finding.id)},
        {"finding_type": "compliance", "finding_id": str(compliance_finding.id)},
    ]

    audit_events = db_session.query(AuditEvent).filter(AuditEvent.case_id == case.id).all()
    assert any(event.event_type == AuditEventType.DECISION_RECORDED for event in audit_events)


def test_approve_case_creates_decision_and_closes_case(client, db_session) -> None:
    reviewer_id = uuid4()
    case, document, extraction_result = _seed_decision_case(db_session, case_status=CaseStatus.DECISION_READY)
    validation_finding, _, _ = _seed_findings(db_session, case=case, document=document, extraction_result=extraction_result)

    response = client.post(
        f"/api/v1/cases/{case.id}/decisions/approve",
        json={
            "decided_by_user_id": str(reviewer_id),
            "decision_type": "reviewer_decision",
            "reason_code": "all_checks_passed",
            "rationale": "Validation findings cleared by reviewer evidence check.",
            "linked_findings": [{"finding_type": "validation", "finding_id": str(validation_finding.id)}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_status"] == "approved"
    assert payload["decision"]["outcome"] == "approved"

    refreshed_case = db_session.get(Case, case.id)
    assert refreshed_case is not None
    assert refreshed_case.status == CaseStatus.APPROVED
    assert refreshed_case.closed_at is not None


def test_reject_case_creates_decision_and_updates_status(client, db_session) -> None:
    reviewer_id = uuid4()
    case, document, extraction_result = _seed_decision_case(db_session, case_status=CaseStatus.DECISION_READY)
    _, risk_finding, _ = _seed_findings(db_session, case=case, document=document, extraction_result=extraction_result)

    response = client.post(
        f"/api/v1/cases/{case.id}/decisions/reject",
        json={
            "decided_by_user_id": str(reviewer_id),
            "decision_type": "supervisor_decision",
            "reason_code": "risk_threshold_exceeded",
            "rationale": "Risk posture exceeds the allowed threshold.",
            "linked_findings": [{"finding_type": "risk", "finding_id": str(risk_finding.id)}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_status"] == "rejected"
    assert payload["decision"]["outcome"] == "rejected"

    refreshed_case = db_session.get(Case, case.id)
    assert refreshed_case is not None
    assert refreshed_case.status == CaseStatus.REJECTED
    assert refreshed_case.closed_at is not None


def test_request_more_review_moves_case_back_to_manual_review(client, db_session) -> None:
    reviewer_id = uuid4()
    case, document, extraction_result = _seed_decision_case(db_session, case_status=CaseStatus.DECISION_READY)
    _, _, compliance_finding = _seed_findings(db_session, case=case, document=document, extraction_result=extraction_result)

    response = client.post(
        f"/api/v1/cases/{case.id}/decisions/request-review",
        json={
            "decided_by_user_id": str(reviewer_id),
            "decision_type": "reviewer_decision",
            "reason_code": "supervisor_review_required",
            "rationale": "Additional operations review is required before approval.",
            "linked_findings": [{"finding_type": "compliance", "finding_id": str(compliance_finding.id)}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_status"] == "manual_review_required"
    assert payload["decision"]["outcome"] == "review_required"
    assert "decision_ready" in payload["allowed_next_statuses"]


def test_approve_case_rejects_invalid_case_status(client, db_session) -> None:
    reviewer_id = uuid4()
    case, _, _ = _seed_decision_case(db_session, case_status=CaseStatus.MANUAL_REVIEW_REQUIRED)

    response = client.post(
        f"/api/v1/cases/{case.id}/decisions/approve",
        json={
            "decided_by_user_id": str(reviewer_id),
            "decision_type": "reviewer_decision",
            "reason_code": "manual_override",
        },
    )

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "decision_not_allowed_for_case_status"
    assert "manual_review_required" in error["message"]


def test_create_decision_rejects_missing_linked_finding(client, db_session) -> None:
    reviewer_id = uuid4()
    case, _, _ = _seed_decision_case(db_session, case_status=CaseStatus.DECISION_READY)

    response = client.post(
        f"/api/v1/cases/{case.id}/decisions",
        json={
            "decided_by_user_id": str(reviewer_id),
            "decision_type": "reviewer_decision",
            "outcome": "review_required",
            "reason_code": "evidence_gap",
            "linked_findings": [{"finding_type": "validation", "finding_id": str(uuid4())}],
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource_not_found"

from __future__ import annotations

from sqlalchemy import UniqueConstraint, inspect as sa_inspect

from ops_agent.infrastructure.db.base import Base
from ops_agent.infrastructure.db.models import (
    AuditEvent,
    Case,
    ComplianceFinding,
    Decision,
    Document,
    ExtractionResult,
    ManualReviewAction,
    OCRResult,
    RiskFinding,
    Role,
    User,
    ValidationFinding,
)


def test_core_tables_are_registered() -> None:
    table_names = set(Base.metadata.tables.keys())

    assert {
        "audit_events",
        "cases",
        "compliance_findings",
        "decisions",
        "documents",
        "extraction_results",
        "manual_review_actions",
        "ocr_results",
        "risk_findings",
        "roles",
        "user_roles",
        "users",
        "validation_findings",
    }.issubset(table_names)


def test_case_document_and_output_relationships_are_traceable() -> None:
    case_relationships = set(sa_inspect(Case).relationships.keys())
    document_relationships = set(sa_inspect(Document).relationships.keys())
    extraction_relationships = set(sa_inspect(ExtractionResult).relationships.keys())

    assert {"documents", "validation_findings", "risk_findings", "compliance_findings", "decisions"}.issubset(
        case_relationships
    )
    assert {"case", "ocr_results", "extraction_results", "manual_review_actions"}.issubset(document_relationships)
    assert {"document", "ocr_result", "validation_findings", "risk_findings", "compliance_findings"}.issubset(
        extraction_relationships
    )


def test_review_identity_and_audit_relationships_are_present() -> None:
    user_relationships = set(sa_inspect(User).relationships.keys())
    decision_relationships = set(sa_inspect(Decision).relationships.keys())
    audit_relationships = set(sa_inspect(AuditEvent).relationships.keys())
    role_relationships = set(sa_inspect(Role).relationships.keys())

    assert {"roles", "submitted_cases", "uploaded_documents", "manual_review_actions", "audit_events"}.issubset(
        user_relationships
    )
    assert {"case", "decided_by_user", "manual_review_actions"}.issubset(decision_relationships)
    assert {"case", "actor_user"}.issubset(audit_relationships)
    assert {"users"} == role_relationships


def test_mvp_and_future_field_metadata_are_marked() -> None:
    assert Case.__table__.c.case_reference.info["delivery_phase"] == "mvp_required"
    assert Document.__table__.c.storage_key.info["delivery_phase"] == "mvp_required"
    assert OCRResult.__table__.c.provider_job_id.info["delivery_phase"] == "future"
    assert ValidationFinding.__table__.c.evidence_refs.info["delivery_phase"] == "mvp_required"
    assert RiskFinding.__table__.c.risk_score.info["delivery_phase"] == "future"
    assert ComplianceFinding.__table__.c.regulation_reference.info["delivery_phase"] == "future"
    assert ManualReviewAction.__table__.c.payload.info["delivery_phase"] == "mvp_required"


def test_mvp_indexes_and_constraints_support_ops_lookup_patterns() -> None:
    case_indexes = {index.name for index in Case.__table__.indexes}
    document_indexes = {index.name for index in Document.__table__.indexes}
    extraction_indexes = {index.name for index in ExtractionResult.__table__.indexes}
    validation_indexes = {index.name for index in ValidationFinding.__table__.indexes}
    decision_indexes = {index.name for index in Decision.__table__.indexes}
    manual_review_indexes = {index.name for index in ManualReviewAction.__table__.indexes}
    audit_indexes = {index.name for index in AuditEvent.__table__.indexes}
    document_unique_constraints = {
        constraint.name for constraint in Document.__table__.constraints if isinstance(constraint, UniqueConstraint)
    }

    assert {"ix_cases_status", "ix_cases_current_queue_status", "ix_cases_case_type"}.issubset(case_indexes)
    assert {"ix_documents_case_id_status", "ix_documents_sha256_digest"}.issubset(document_indexes)
    assert {"uq_documents_storage_key"}.issubset(document_unique_constraints)
    assert {"ix_extraction_results_document_status", "ix_extraction_results_schema_name"}.issubset(extraction_indexes)
    assert {"ix_validation_findings_case_status", "ix_validation_findings_extraction_result_id"}.issubset(validation_indexes)
    assert {"ix_decisions_case_id", "ix_decisions_outcome"}.issubset(decision_indexes)
    assert {"ix_manual_review_actions_case_id", "ix_manual_review_actions_case_id_created_at"}.issubset(manual_review_indexes)
    assert {
        "ix_audit_events_case_id_occurred_at",
        "ix_audit_events_case_id_event_type",
        "ix_audit_events_resource_type_resource_id",
    }.issubset(audit_indexes)

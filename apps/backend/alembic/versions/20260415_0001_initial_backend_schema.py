"""Initial Ops Agent backend schema.

Revision ID: 20260415_0001
Revises:
Create Date: 2026-04-15 12:50:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260415_0001"
down_revision = None
branch_labels = None
depends_on = None


case_status_enum = sa.Enum(
    "created",
    "documents_uploaded",
    "queued_for_processing",
    "processing",
    "extraction_completed",
    "validation_completed",
    "manual_review_required",
    "decision_ready",
    "approved",
    "rejected",
    "failed",
    name="casestatus",
    native_enum=False,
)
document_status_enum = sa.Enum(
    "uploaded",
    "stored",
    "ocr_pending",
    "ocr_completed",
    "extraction_completed",
    "review_required",
    "failed",
    "archived",
    name="documentstatus",
    native_enum=False,
)
processing_status_enum = sa.Enum(
    "pending",
    "in_progress",
    "completed",
    "failed",
    name="processingstatus",
    native_enum=False,
)
finding_severity_enum = sa.Enum(
    "info",
    "warning",
    "error",
    "critical",
    name="findingseverity",
    native_enum=False,
)
finding_status_enum = sa.Enum(
    "open",
    "resolved",
    "waived",
    name="findingstatus",
    native_enum=False,
)
risk_level_enum = sa.Enum(
    "low",
    "medium",
    "high",
    "critical",
    name="risklevel",
    native_enum=False,
)
decision_type_enum = sa.Enum(
    "system_recommendation",
    "reviewer_decision",
    "supervisor_decision",
    name="decisiontype",
    native_enum=False,
)
decision_outcome_enum = sa.Enum(
    "approved",
    "rejected",
    "review_required",
    "escalated",
    name="decisionoutcome",
    native_enum=False,
)
manual_review_action_type_enum = sa.Enum(
    "add_note",
    "claim",
    "unclaim",
    "confirm_extraction",
    "correct_data",
    "request_reprocessing",
    "escalate",
    "approve",
    "reject",
    "close",
    name="manualreviewactiontype",
    native_enum=False,
)
audit_actor_type_enum = sa.Enum(
    "system",
    "user",
    "service",
    name="auditactortype",
    native_enum=False,
)
audit_event_type_enum = sa.Enum(
    "case_created",
    "document_added",
    "document_upload_rejected",
    "document_downloaded",
    "ocr_completed",
    "extraction_completed",
    "finding_created",
    "decision_recorded",
    "manual_review_action_recorded",
    "status_changed",
    name="auditeventtype",
    native_enum=False,
)
user_status_enum = sa.Enum(
    "active",
    "disabled",
    "locked",
    name="userstatus",
    native_enum=False,
)
role_code_enum = sa.Enum(
    "ops_user",
    "reviewer",
    "compliance_user",
    "admin",
    name="rolecode",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("code", role_code_enum, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
        sa.UniqueConstraint("code", name="uq_roles_code"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=150), nullable=False),
        sa.Column("status", user_status_enum, nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )

    op.create_table(
        "healthcheck_probes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("probe_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_healthcheck_probes")),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name=op.f("fk_user_roles_role_id_roles"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_user_roles_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id", name=op.f("pk_user_roles")),
    )

    op.create_table(
        "cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("case_reference", sa.String(length=64), nullable=False),
        sa.Column("case_type", sa.String(length=80), nullable=False),
        sa.Column("status", case_status_enum, nullable=False),
        sa.Column("status_changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_queue", sa.String(length=80), nullable=False),
        sa.Column("source_channel", sa.String(length=80), nullable=False),
        sa.Column("customer_reference", sa.String(length=120), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("case_metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["submitted_by_user_id"],
            ["users.id"],
            name=op.f("fk_cases_submitted_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cases")),
        sa.UniqueConstraint("case_reference", name="uq_cases_case_reference"),
    )
    op.create_index("ix_cases_status", "cases", ["status"], unique=False)
    op.create_index("ix_cases_current_queue_status", "cases", ["current_queue", "status"], unique=False)
    op.create_index("ix_cases_case_type", "cases", ["case_type"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("document_type", sa.String(length=80), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("sha256_digest", sa.String(length=128), nullable=False),
        sa.Column("status", document_status_enum, nullable=False),
        sa.Column("status_changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_channel", sa.String(length=80), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("uploaded_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("document_metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_documents_case_id_cases"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["uploaded_by_user_id"],
            ["users.id"],
            name=op.f("fk_documents_uploaded_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
        sa.UniqueConstraint("storage_key", name="uq_documents_storage_key"),
    )
    op.create_index("ix_documents_case_id_status", "documents", ["case_id", "status"], unique=False)
    op.create_index("ix_documents_sha256_digest", "documents", ["sha256_digest"], unique=False)

    op.create_table(
        "ocr_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("status", processing_status_enum, nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("provider_name", sa.String(length=100), nullable=False),
        sa.Column("provider_job_id", sa.String(length=120), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("result_metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_ocr_results_document_id_documents"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ocr_results")),
    )
    op.create_index("ix_ocr_results_document_status", "ocr_results", ["document_id", "status"], unique=False)

    op.create_table(
        "extraction_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("ocr_result_id", sa.Uuid(), nullable=True),
        sa.Column("status", processing_status_enum, nullable=False),
        sa.Column("schema_name", sa.String(length=120), nullable=False),
        sa.Column("extracted_payload", sa.JSON(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("evidence_refs", sa.JSON(), nullable=False),
        sa.Column("provider_name", sa.String(length=100), nullable=False),
        sa.Column("provider_job_id", sa.String(length=120), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("model_version", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_extraction_results_document_id_documents"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ocr_result_id"],
            ["ocr_results.id"],
            name=op.f("fk_extraction_results_ocr_result_id_ocr_results"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_extraction_results")),
    )
    op.create_index("ix_extraction_results_document_status", "extraction_results", ["document_id", "status"], unique=False)
    op.create_index("ix_extraction_results_schema_name", "extraction_results", ["schema_name"], unique=False)

    op.create_table(
        "validation_findings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("extraction_result_id", sa.Uuid(), nullable=True),
        sa.Column("rule_code", sa.String(length=100), nullable=False),
        sa.Column("field_name", sa.String(length=100), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("severity", finding_severity_enum, nullable=False),
        sa.Column("status", finding_status_enum, nullable=False),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("evidence_refs", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_validation_findings_case_id_cases"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_validation_findings_document_id_documents"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["extraction_result_id"],
            ["extraction_results.id"],
            name=op.f("fk_validation_findings_extraction_result_id_extraction_results"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_validation_findings")),
    )
    op.create_index("ix_validation_findings_case_status", "validation_findings", ["case_id", "status"], unique=False)
    op.create_index("ix_validation_findings_extraction_result_id", "validation_findings", ["extraction_result_id"], unique=False)

    op.create_table(
        "risk_findings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("extraction_result_id", sa.Uuid(), nullable=True),
        sa.Column("risk_code", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("risk_level", risk_level_enum, nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("status", finding_status_enum, nullable=False),
        sa.Column("evidence_refs", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_risk_findings_case_id_cases"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_risk_findings_document_id_documents"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["extraction_result_id"],
            ["extraction_results.id"],
            name=op.f("fk_risk_findings_extraction_result_id_extraction_results"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_risk_findings")),
    )
    op.create_index("ix_risk_findings_case_status", "risk_findings", ["case_id", "status"], unique=False)

    op.create_table(
        "compliance_findings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("extraction_result_id", sa.Uuid(), nullable=True),
        sa.Column("policy_code", sa.String(length=100), nullable=False),
        sa.Column("regulation_reference", sa.String(length=120), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("severity", finding_severity_enum, nullable=False),
        sa.Column("status", finding_status_enum, nullable=False),
        sa.Column("evidence_refs", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name=op.f("fk_compliance_findings_case_id_cases"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_compliance_findings_document_id_documents"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["extraction_result_id"],
            ["extraction_results.id"],
            name=op.f("fk_compliance_findings_extraction_result_id_extraction_results"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_compliance_findings")),
    )
    op.create_index("ix_compliance_findings_case_status", "compliance_findings", ["case_id", "status"], unique=False)

    op.create_table(
        "decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("decided_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("decision_type", decision_type_enum, nullable=False),
        sa.Column("outcome", decision_outcome_enum, nullable=False),
        sa.Column("reason_code", sa.String(length=100), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("evidence_refs", sa.JSON(), nullable=False),
        sa.Column("linked_findings", sa.JSON(), nullable=False),
        sa.Column("supersedes_decision_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_decisions_case_id_cases"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["decided_by_user_id"],
            ["users.id"],
            name=op.f("fk_decisions_decided_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_decision_id"],
            ["decisions.id"],
            name=op.f("fk_decisions_supersedes_decision_id_decisions"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_decisions")),
    )
    op.create_index("ix_decisions_case_id", "decisions", ["case_id"], unique=False)
    op.create_index("ix_decisions_outcome", "decisions", ["outcome"], unique=False)

    op.create_table(
        "manual_review_actions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("performed_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("related_decision_id", sa.Uuid(), nullable=True),
        sa.Column("action_type", manual_review_action_type_enum, nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("evidence_refs", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_manual_review_actions_case_id_cases"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_manual_review_actions_document_id_documents"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["performed_by_user_id"],
            ["users.id"],
            name=op.f("fk_manual_review_actions_performed_by_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["related_decision_id"],
            ["decisions.id"],
            name=op.f("fk_manual_review_actions_related_decision_id_decisions"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_manual_review_actions")),
    )
    op.create_index("ix_manual_review_actions_case_id", "manual_review_actions", ["case_id"], unique=False)
    op.create_index("ix_manual_review_actions_case_id_created_at", "manual_review_actions", ["case_id", "created_at"], unique=False)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("case_id", sa.Uuid(), nullable=True),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("actor_type", audit_actor_type_enum, nullable=False),
        sa.Column("actor_identifier", sa.String(length=120), nullable=True),
        sa.Column("event_type", audit_event_type_enum, nullable=False),
        sa.Column("summary", sa.String(length=255), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("evidence_refs", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name=op.f("fk_audit_events_actor_user_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name=op.f("fk_audit_events_case_id_cases"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
    )
    op.create_index("ix_audit_events_case_id_occurred_at", "audit_events", ["case_id", "occurred_at"], unique=False)
    op.create_index("ix_audit_events_case_id_event_type", "audit_events", ["case_id", "event_type"], unique=False)
    op.create_index("ix_audit_events_resource_type_resource_id", "audit_events", ["resource_type", "resource_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_events_resource_type_resource_id", table_name="audit_events")
    op.drop_index("ix_audit_events_case_id_event_type", table_name="audit_events")
    op.drop_index("ix_audit_events_case_id_occurred_at", table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index("ix_manual_review_actions_case_id_created_at", table_name="manual_review_actions")
    op.drop_index("ix_manual_review_actions_case_id", table_name="manual_review_actions")
    op.drop_table("manual_review_actions")

    op.drop_index("ix_decisions_outcome", table_name="decisions")
    op.drop_index("ix_decisions_case_id", table_name="decisions")
    op.drop_table("decisions")

    op.drop_index("ix_compliance_findings_case_status", table_name="compliance_findings")
    op.drop_table("compliance_findings")

    op.drop_index("ix_risk_findings_case_status", table_name="risk_findings")
    op.drop_table("risk_findings")

    op.drop_index("ix_validation_findings_extraction_result_id", table_name="validation_findings")
    op.drop_index("ix_validation_findings_case_status", table_name="validation_findings")
    op.drop_table("validation_findings")

    op.drop_index("ix_extraction_results_schema_name", table_name="extraction_results")
    op.drop_index("ix_extraction_results_document_status", table_name="extraction_results")
    op.drop_table("extraction_results")

    op.drop_index("ix_ocr_results_document_status", table_name="ocr_results")
    op.drop_table("ocr_results")

    op.drop_index("ix_documents_sha256_digest", table_name="documents")
    op.drop_index("ix_documents_case_id_status", table_name="documents")
    op.drop_table("documents")

    op.drop_index("ix_cases_case_type", table_name="cases")
    op.drop_index("ix_cases_current_queue_status", table_name="cases")
    op.drop_index("ix_cases_status", table_name="cases")
    op.drop_table("cases")

    op.drop_table("user_roles")
    op.drop_table("healthcheck_probes")
    op.drop_table("users")
    op.drop_table("roles")

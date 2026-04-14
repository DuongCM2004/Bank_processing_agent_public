from __future__ import annotations

from enum import StrEnum


class AppRole(StrEnum):
    OPS_REVIEWER = "ops_reviewer"
    OPS_SUPERVISOR = "ops_supervisor"
    COMPLIANCE_REVIEWER = "compliance_reviewer"
    FRAUD_REVIEWER = "fraud_reviewer"
    OPS_ADMIN = "ops_admin"
    AUDIT_READER = "audit_reader"
    WORKFLOW_WORKER = "workflow_worker"
    INTEGRATION_SERVICE = "integration_service"


class ProtectedAction(StrEnum):
    CREATE_CASE = "create_case"
    UPLOAD_DOCUMENT = "upload_document"
    VIEW_CASE = "view_case"
    VIEW_DOCUMENT = "view_document"
    CLAIM_REVIEW_TASK = "claim_review_task"
    SUBMIT_CORRECTION = "submit_correction"
    ESCALATE_CASE = "escalate_case"
    CLOSE_CASE = "close_case"
    READ_AUDIT = "read_audit"
    START_WORKFLOW = "start_workflow"
    SIGNAL_WORKFLOW = "signal_workflow"


ROLE_ACCESS_MATRIX: dict[ProtectedAction, tuple[AppRole, ...]] = {
    ProtectedAction.CREATE_CASE: (
        AppRole.OPS_REVIEWER,
        AppRole.OPS_SUPERVISOR,
        AppRole.COMPLIANCE_REVIEWER,
        AppRole.FRAUD_REVIEWER,
        AppRole.OPS_ADMIN,
    ),
    ProtectedAction.UPLOAD_DOCUMENT: (
        AppRole.OPS_REVIEWER,
        AppRole.OPS_SUPERVISOR,
        AppRole.COMPLIANCE_REVIEWER,
        AppRole.FRAUD_REVIEWER,
        AppRole.OPS_ADMIN,
    ),
    ProtectedAction.VIEW_CASE: (
        AppRole.OPS_REVIEWER,
        AppRole.OPS_SUPERVISOR,
        AppRole.COMPLIANCE_REVIEWER,
        AppRole.FRAUD_REVIEWER,
        AppRole.OPS_ADMIN,
        AppRole.AUDIT_READER,
    ),
    ProtectedAction.VIEW_DOCUMENT: (
        AppRole.OPS_REVIEWER,
        AppRole.OPS_SUPERVISOR,
        AppRole.COMPLIANCE_REVIEWER,
        AppRole.FRAUD_REVIEWER,
        AppRole.OPS_ADMIN,
        AppRole.AUDIT_READER,
    ),
    ProtectedAction.CLAIM_REVIEW_TASK: (
        AppRole.OPS_REVIEWER,
        AppRole.OPS_SUPERVISOR,
        AppRole.COMPLIANCE_REVIEWER,
        AppRole.FRAUD_REVIEWER,
    ),
    ProtectedAction.SUBMIT_CORRECTION: (
        AppRole.OPS_REVIEWER,
        AppRole.OPS_SUPERVISOR,
        AppRole.COMPLIANCE_REVIEWER,
        AppRole.FRAUD_REVIEWER,
    ),
    ProtectedAction.ESCALATE_CASE: (
        AppRole.OPS_REVIEWER,
        AppRole.OPS_SUPERVISOR,
        AppRole.COMPLIANCE_REVIEWER,
        AppRole.FRAUD_REVIEWER,
    ),
    ProtectedAction.CLOSE_CASE: (
        AppRole.OPS_SUPERVISOR,
        AppRole.COMPLIANCE_REVIEWER,
        AppRole.FRAUD_REVIEWER,
        AppRole.OPS_ADMIN,
    ),
    ProtectedAction.READ_AUDIT: (
        AppRole.OPS_SUPERVISOR,
        AppRole.OPS_ADMIN,
        AppRole.AUDIT_READER,
    ),
    ProtectedAction.START_WORKFLOW: (
        AppRole.WORKFLOW_WORKER,
        AppRole.INTEGRATION_SERVICE,
    ),
    ProtectedAction.SIGNAL_WORKFLOW: (
        AppRole.WORKFLOW_WORKER,
        AppRole.INTEGRATION_SERVICE,
    ),
}


REQUIRED_API_SECURITY_HEADERS: tuple[str, ...] = (
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Content-Security-Policy",
)


ALLOWED_UPLOAD_MIME_TYPES: tuple[str, ...] = (
    "application/pdf",
    "image/png",
    "image/jpeg",
)

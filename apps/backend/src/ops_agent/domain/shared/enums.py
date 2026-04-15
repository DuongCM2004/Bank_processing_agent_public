from __future__ import annotations

from enum import StrEnum


class CaseStatus(StrEnum):
    CREATED = "created"
    DOCUMENTS_UPLOADED = "documents_uploaded"
    QUEUED_FOR_PROCESSING = "queued_for_processing"
    PROCESSING = "processing"
    EXTRACTION_COMPLETED = "extraction_completed"
    VALIDATION_COMPLETED = "validation_completed"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    DECISION_READY = "decision_ready"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    STORED = "stored"
    OCR_PENDING = "ocr_pending"
    OCR_COMPLETED = "ocr_completed"
    EXTRACTION_COMPLETED = "extraction_completed"
    REVIEW_REQUIRED = "review_required"
    FAILED = "failed"
    ARCHIVED = "archived"


class ProcessingStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class FindingSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class FindingStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    WAIVED = "waived"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionType(StrEnum):
    SYSTEM_RECOMMENDATION = "system_recommendation"
    REVIEWER_DECISION = "reviewer_decision"
    SUPERVISOR_DECISION = "supervisor_decision"


class DecisionOutcome(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REVIEW_REQUIRED = "review_required"
    ESCALATED = "escalated"


class ManualReviewActionType(StrEnum):
    ADD_NOTE = "add_note"
    CLAIM = "claim"
    UNCLAIM = "unclaim"
    CONFIRM_EXTRACTION = "confirm_extraction"
    CORRECT_DATA = "correct_data"
    REQUEST_REPROCESSING = "request_reprocessing"
    ESCALATE = "escalate"
    APPROVE = "approve"
    REJECT = "reject"
    CLOSE = "close"


class AuditActorType(StrEnum):
    SYSTEM = "system"
    USER = "user"
    SERVICE = "service"


class AuditEventType(StrEnum):
    CASE_CREATED = "case_created"
    DOCUMENT_ADDED = "document_added"
    DOCUMENT_DOWNLOADED = "document_downloaded"
    OCR_COMPLETED = "ocr_completed"
    EXTRACTION_COMPLETED = "extraction_completed"
    FINDING_CREATED = "finding_created"
    DECISION_RECORDED = "decision_recorded"
    MANUAL_REVIEW_ACTION_RECORDED = "manual_review_action_recorded"
    STATUS_CHANGED = "status_changed"


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    LOCKED = "locked"


class RoleCode(StrEnum):
    OPS_REVIEWER = "ops_reviewer"
    OPS_SUPERVISOR = "ops_supervisor"
    COMPLIANCE_OFFICER = "compliance_officer"
    RISK_ANALYST = "risk_analyst"
    PLATFORM_ADMIN = "platform_admin"

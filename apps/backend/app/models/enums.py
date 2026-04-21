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
    QUEUED = "queued"
    PREPROCESSING = "preprocessing"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    RETRYING = "retrying"
    EXTRACTED = "extracted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PERSISTED = "persisted"
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
    OCR_COMPLETED = "ocr_completed"
    EXTRACTION_COMPLETED = "extraction_completed"
    VALIDATION_COMPLETED = "validation_completed"
    FINDING_CREATED = "finding_created"
    DECISION_RECORDED = "decision_recorded"
    MANUAL_REVIEW_ACTION_RECORDED = "manual_review_action_recorded"
    STATUS_CHANGED = "status_changed"
    PROCESSING_QUEUED = "processing_queued"
    DOCUMENT_QUEUED = "document_queued"
    DOCUMENT_REVIEW_STARTED = "document_review_started"
    DOCUMENT_APPROVED = "document_approved"
    DOCUMENT_REJECTED = "document_rejected"
    DOCUMENT_PERSISTED = "document_persisted"
    DOCUMENT_FAILED = "document_failed"


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    LOCKED = "locked"


class RoleCode(StrEnum):
    OPS_USER = "ops_user"
    REVIEWER = "reviewer"
    COMPLIANCE_USER = "compliance_user"
    ADMIN = "admin"

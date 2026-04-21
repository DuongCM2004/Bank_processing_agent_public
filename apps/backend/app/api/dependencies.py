from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.audit.logger import AuditLogger
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.repositories.audit import AuditEventRepository
from app.repositories.cases import CaseRepository
from app.repositories.decisions import DecisionRepository
from app.repositories.documents import DocumentRepository, ProcessingResultRepository
from app.repositories.manual_review import ManualReviewRepository
from app.services.audit import AuditService
from app.services.cases import CaseService
from app.services.decisions import DecisionService
from app.services.documents import DocumentService
from app.services.manual_review import ManualReviewService
from app.services.processing import ProcessingService

DbSession = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_audit_logger(db: DbSession) -> AuditLogger:
    return AuditLogger(AuditEventRepository(db))


def get_case_service(db: DbSession, audit_logger: Annotated[AuditLogger, Depends(get_audit_logger)]) -> CaseService:
    return CaseService(CaseRepository(db), audit_logger)


def get_document_service(
    db: DbSession,
    settings: SettingsDep,
    audit_logger: Annotated[AuditLogger, Depends(get_audit_logger)],
    case_service: Annotated[CaseService, Depends(get_case_service)],
) -> DocumentService:
    return DocumentService(
        DocumentRepository(db),
        ProcessingResultRepository(db),
        ManualReviewRepository(db),
        CaseRepository(db),
        case_service,
        audit_logger,
        settings,
    )


def get_processing_service(
    db: DbSession,
    audit_logger: Annotated[AuditLogger, Depends(get_audit_logger)],
    case_service: Annotated[CaseService, Depends(get_case_service)],
) -> ProcessingService:
    return ProcessingService(
        CaseRepository(db),
        DocumentRepository(db),
        ProcessingResultRepository(db),
        case_service,
        audit_logger,
    )


def get_decision_service(
    db: DbSession,
    audit_logger: Annotated[AuditLogger, Depends(get_audit_logger)],
    case_service: Annotated[CaseService, Depends(get_case_service)],
) -> DecisionService:
    return DecisionService(
        DecisionRepository(db),
        CaseRepository(db),
        case_service,
        audit_logger,
    )


def get_manual_review_service(
    db: DbSession,
    audit_logger: Annotated[AuditLogger, Depends(get_audit_logger)],
    case_service: Annotated[CaseService, Depends(get_case_service)],
) -> ManualReviewService:
    return ManualReviewService(
        ManualReviewRepository(db),
        DocumentRepository(db),
        ProcessingResultRepository(db),
        CaseRepository(db),
        case_service,
        audit_logger,
    )


def get_audit_service(db: DbSession) -> AuditService:
    return AuditService(AuditEventRepository(db))


CaseServiceDep = Annotated[CaseService, Depends(get_case_service)]
DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
ProcessingServiceDep = Annotated[ProcessingService, Depends(get_processing_service)]
DecisionServiceDep = Annotated[DecisionService, Depends(get_decision_service)]
ManualReviewServiceDep = Annotated[ManualReviewService, Depends(get_manual_review_service)]
AuditServiceDep = Annotated[AuditService, Depends(get_audit_service)]

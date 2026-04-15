from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from ops_agent.application.services.case_management import (
    CaseManagementService,
    SQLAlchemyCaseTransitionAuditHook,
)
from ops_agent.application.services.audit import AuditService
from ops_agent.application.services.case_processing import (
    CaseProcessingService,
    SQLAlchemyCaseProcessingTransitionAuditHook,
)
from ops_agent.application.services.case_workflow import CaseWorkflowService
from ops_agent.application.services.decision import DecisionService
from ops_agent.application.services.document_access import DocumentAccessService
from ops_agent.application.services.document_upload import DocumentUploadService
from ops_agent.application.services.manual_review import ManualReviewService
from ops_agent.application.services.system_health import SystemHealthService
from ops_agent.config import AppSettings, get_settings
from ops_agent.domain.shared.exceptions import OpsAgentError
from ops_agent.infrastructure.db.repositories import AuditRepository, CaseRepository, DecisionRepository, ManualReviewRepository, ProcessingRepository
from ops_agent.infrastructure.db.repositories.document_repository import DocumentRepository
from ops_agent.infrastructure.providers import (
    PlaceholderDocumentClassificationProvider,
    PlaceholderExtractionProvider,
    PlaceholderOCRProvider,
    PlaceholderValidationRulesEngine,
)
from ops_agent.infrastructure.providers.interfaces import (
    DocumentClassificationProvider,
    ExtractionProvider,
    OCRProvider,
    ValidationRulesEngine,
)
from ops_agent.infrastructure.db.session import get_db_session
from ops_agent.infrastructure.queue.contracts import TaskDispatcher
from ops_agent.infrastructure.storage import LocalDocumentStorage
from ops_agent.infrastructure.storage.protocols import DocumentStorage


def get_app_settings() -> AppSettings:
    return get_settings()


def get_system_health_service(
    settings: Annotated[AppSettings, Depends(get_app_settings)],
    session: Annotated[Session, Depends(get_db_session)],
) -> SystemHealthService:
    return SystemHealthService(settings=settings, session=session)


def get_case_repository(session: Annotated[Session, Depends(get_db_session)]) -> CaseRepository:
    return CaseRepository(session)


def get_audit_repository(session: Annotated[Session, Depends(get_db_session)]) -> AuditRepository:
    return AuditRepository(session)


def get_audit_service(repository: Annotated[AuditRepository, Depends(get_audit_repository)]) -> AuditService:
    return AuditService(repository)


def get_case_workflow_service(
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> CaseWorkflowService:
    return CaseWorkflowService(audit_hooks=(SQLAlchemyCaseTransitionAuditHook(audit_service),))


def get_case_management_service(
    repository: Annotated[CaseRepository, Depends(get_case_repository)],
    workflow_service: Annotated[CaseWorkflowService, Depends(get_case_workflow_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> CaseManagementService:
    return CaseManagementService(repository=repository, workflow_service=workflow_service, audit_service=audit_service)


def get_document_repository(session: Annotated[Session, Depends(get_db_session)]) -> DocumentRepository:
    return DocumentRepository(session)


def get_processing_repository(session: Annotated[Session, Depends(get_db_session)]) -> ProcessingRepository:
    return ProcessingRepository(session)


def get_manual_review_repository(session: Annotated[Session, Depends(get_db_session)]) -> ManualReviewRepository:
    return ManualReviewRepository(session)


def get_decision_repository(session: Annotated[Session, Depends(get_db_session)]) -> DecisionRepository:
    return DecisionRepository(session)


def get_document_storage(settings: Annotated[AppSettings, Depends(get_app_settings)]) -> DocumentStorage:
    if settings.storage.backend == "local":
        return LocalDocumentStorage(settings.storage.root_path)
    raise OpsAgentError(
        f"Unsupported storage backend '{settings.storage.backend}'.",
        error_code="unsupported_storage_backend",
        status_code=500,
    )


def get_document_upload_service(
    repository: Annotated[DocumentRepository, Depends(get_document_repository)],
    storage: Annotated[DocumentStorage, Depends(get_document_storage)],
    settings: Annotated[AppSettings, Depends(get_app_settings)],
    workflow_service: Annotated[CaseWorkflowService, Depends(get_case_workflow_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> DocumentUploadService:
    return DocumentUploadService(
        repository=repository,
        storage=storage,
        storage_settings=settings.storage,
        workflow_service=workflow_service,
        audit_service=audit_service,
    )


def get_document_access_service(
    repository: Annotated[DocumentRepository, Depends(get_document_repository)],
    storage: Annotated[DocumentStorage, Depends(get_document_storage)],
) -> DocumentAccessService:
    return DocumentAccessService(repository=repository, storage=storage)


def get_ocr_provider(settings: Annotated[AppSettings, Depends(get_app_settings)]) -> OCRProvider:
    if settings.ai.provider_mode == "placeholder":
        return PlaceholderOCRProvider()
    raise OpsAgentError(
        f"OCR provider mode '{settings.ai.provider_mode}' is not configured.",
        error_code="unsupported_ocr_provider_mode",
        status_code=500,
    )


def get_extraction_provider(settings: Annotated[AppSettings, Depends(get_app_settings)]) -> ExtractionProvider:
    if settings.ai.provider_mode == "placeholder":
        return PlaceholderExtractionProvider()
    raise OpsAgentError(
        f"Extraction provider mode '{settings.ai.provider_mode}' is not configured.",
        error_code="unsupported_extraction_provider_mode",
        status_code=500,
    )


def get_document_classification_provider(
    settings: Annotated[AppSettings, Depends(get_app_settings)],
) -> DocumentClassificationProvider:
    if settings.ai.provider_mode == "placeholder":
        return PlaceholderDocumentClassificationProvider()
    raise OpsAgentError(
        f"Document classification provider mode '{settings.ai.provider_mode}' is not configured.",
        error_code="unsupported_document_classification_provider_mode",
        status_code=500,
    )


def get_validation_rules_engine(settings: Annotated[AppSettings, Depends(get_app_settings)]) -> ValidationRulesEngine:
    if settings.ai.provider_mode == "placeholder":
        return PlaceholderValidationRulesEngine()
    raise OpsAgentError(
        f"Validation rules engine mode '{settings.ai.provider_mode}' is not configured.",
        error_code="unsupported_validation_rules_engine_mode",
        status_code=500,
    )


def get_task_dispatcher() -> TaskDispatcher | None:
    return None


def get_case_processing_service(
    repository: Annotated[ProcessingRepository, Depends(get_processing_repository)],
    settings: Annotated[AppSettings, Depends(get_app_settings)],
    storage: Annotated[DocumentStorage, Depends(get_document_storage)],
    ocr_provider: Annotated[OCRProvider, Depends(get_ocr_provider)],
    classification_provider: Annotated[DocumentClassificationProvider, Depends(get_document_classification_provider)],
    extraction_provider: Annotated[ExtractionProvider, Depends(get_extraction_provider)],
    validation_engine: Annotated[ValidationRulesEngine, Depends(get_validation_rules_engine)],
    task_dispatcher: Annotated[TaskDispatcher | None, Depends(get_task_dispatcher)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> CaseProcessingService:
    workflow_service = CaseWorkflowService(audit_hooks=(SQLAlchemyCaseProcessingTransitionAuditHook(repository),))
    return CaseProcessingService(
        repository=repository,
        workflow_service=workflow_service,
        storage=storage,
        ocr_provider=ocr_provider,
        classification_provider=classification_provider,
        extraction_provider=extraction_provider,
        validation_engine=validation_engine,
        processing_settings=settings.processing,
        worker_settings=settings.worker,
        task_dispatcher=task_dispatcher,
    )


def get_manual_review_service(
    repository: Annotated[ManualReviewRepository, Depends(get_manual_review_repository)],
    workflow_service: Annotated[CaseWorkflowService, Depends(get_case_workflow_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> ManualReviewService:
    return ManualReviewService(repository=repository, workflow_service=workflow_service, audit_service=audit_service)


def get_decision_service(
    repository: Annotated[DecisionRepository, Depends(get_decision_repository)],
    workflow_service: Annotated[CaseWorkflowService, Depends(get_case_workflow_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> DecisionService:
    return DecisionService(repository=repository, workflow_service=workflow_service, audit_service=audit_service)


SettingsDep = Annotated[AppSettings, Depends(get_app_settings)]
DBSessionDep = Annotated[Session, Depends(get_db_session)]
SystemHealthServiceDep = Annotated[SystemHealthService, Depends(get_system_health_service)]
AuditRepositoryDep = Annotated[AuditRepository, Depends(get_audit_repository)]
AuditServiceDep = Annotated[AuditService, Depends(get_audit_service)]
CaseRepositoryDep = Annotated[CaseRepository, Depends(get_case_repository)]
CaseWorkflowServiceDep = Annotated[CaseWorkflowService, Depends(get_case_workflow_service)]
CaseManagementServiceDep = Annotated[CaseManagementService, Depends(get_case_management_service)]
DocumentRepositoryDep = Annotated[DocumentRepository, Depends(get_document_repository)]
DecisionRepositoryDep = Annotated[DecisionRepository, Depends(get_decision_repository)]
ManualReviewRepositoryDep = Annotated[ManualReviewRepository, Depends(get_manual_review_repository)]
ProcessingRepositoryDep = Annotated[ProcessingRepository, Depends(get_processing_repository)]
DocumentAccessServiceDep = Annotated[DocumentAccessService, Depends(get_document_access_service)]
DecisionServiceDep = Annotated[DecisionService, Depends(get_decision_service)]
ManualReviewServiceDep = Annotated[ManualReviewService, Depends(get_manual_review_service)]
CaseProcessingServiceDep = Annotated[CaseProcessingService, Depends(get_case_processing_service)]
DocumentUploadServiceDep = Annotated[DocumentUploadService, Depends(get_document_upload_service)]

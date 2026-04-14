from __future__ import annotations

from ops_agent.application.services.case_application_service import CaseApplicationService
from ops_agent.application.services.processing_application_service import ProcessingApplicationService
from ops_agent.infrastructure.persistence.memory_repository import InMemoryRepository
from ops_agent.service import CaseWorkflowService

repository = InMemoryRepository()
workflow_service = CaseWorkflowService(repository)
case_application_service = CaseApplicationService(workflow_service)
processing_application_service = ProcessingApplicationService(repository)


def get_case_application_service() -> CaseApplicationService:
    return case_application_service


def get_repository() -> InMemoryRepository:
    return repository


def get_processing_application_service() -> ProcessingApplicationService:
    return processing_application_service

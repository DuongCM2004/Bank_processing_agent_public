from __future__ import annotations

from ops_agent.application.services.case_application_service import CaseApplicationService
from ops_agent.models import CaseCreateRequest, CaseCreateResponse


class CreateCaseUseCase:
    def __init__(self, service: CaseApplicationService) -> None:
        self.service = service

    def execute(self, request: CaseCreateRequest) -> CaseCreateResponse:
        return self.service.create_case(request)

from __future__ import annotations

from ops_agent.application.services.case_application_service import CaseApplicationService
from ops_agent.models import CaseResults


class GetCaseResultsUseCase:
    def __init__(self, service: CaseApplicationService) -> None:
        self.service = service

    def execute(self, case_id: str) -> CaseResults:
        return self.service.get_results(case_id)

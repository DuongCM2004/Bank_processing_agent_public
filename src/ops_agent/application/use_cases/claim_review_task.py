from __future__ import annotations

from ops_agent.application.services.case_application_service import CaseApplicationService
from ops_agent.models import ReviewTaskClaimRequest, ReviewTaskRecord


class ClaimReviewTaskUseCase:
    def __init__(self, service: CaseApplicationService) -> None:
        self.service = service

    def execute(self, task_id: str, request: ReviewTaskClaimRequest) -> ReviewTaskRecord:
        return self.service.claim_review_task(task_id, request)

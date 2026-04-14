from __future__ import annotations

from fastapi import APIRouter, Depends

from ops_agent.api.dependencies import get_processing_application_service
from ops_agent.application.services.processing_application_service import ProcessingApplicationService
from ops_agent.workflow_contracts import ReviewCompletionSignal, WorkflowRunStatusResponse, WorkflowStartCommand

router = APIRouter(prefix="/internal/workflows", tags=["internal-workflows"])


@router.post("/start", status_code=202)
def start_workflow(
    request: WorkflowStartCommand,
    service: ProcessingApplicationService = Depends(get_processing_application_service),
) -> dict[str, str]:
    accepted = service.start_from_command(request)
    return {"status": "accepted", "case_id": accepted.case_id, "workflow_run_id": accepted.workflow_run_id}


@router.get("/{case_id}", response_model=WorkflowRunStatusResponse)
def get_workflow_status(
    case_id: str,
    service: ProcessingApplicationService = Depends(get_processing_application_service),
) -> WorkflowRunStatusResponse:
    return service.get_workflow_status(case_id)


@router.post("/{case_id}/signal-review-complete", status_code=202)
def signal_review_complete(
    case_id: str,
    request: ReviewCompletionSignal,
    service: ProcessingApplicationService = Depends(get_processing_application_service),
) -> dict[str, str]:
    return service.signal_review_complete(case_id=case_id, request=request)

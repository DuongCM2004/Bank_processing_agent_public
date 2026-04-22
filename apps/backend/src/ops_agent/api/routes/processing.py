from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from ops_agent.api.dependencies import CaseProcessingServiceDep
from ops_agent.api.openapi import error_responses
from ops_agent.api.schemas import QueueProcessingRequest, QueueProcessingResponse
from ops_agent.domain.shared.enums import CaseStatus
from ops_agent.security.rbac import Permission, require_permission

router = APIRouter(prefix="/cases/{case_id}/processing", tags=["processing"])


@router.post(
    "/queue",
    response_model=QueueProcessingResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue case processing",
    description="Queues a case for document processing and can run the MVP extraction pipeline synchronously for local review workflows.",
    operation_id="queueCaseProcessing",
    responses=error_responses(401, 403, 404, 409, 422, 500),
    dependencies=[Depends(require_permission(Permission.PROCESSING_QUEUE))],
)
def queue_case_processing(
    case_id: UUID,
    request: QueueProcessingRequest,
    processing_service: CaseProcessingServiceDep,
) -> QueueProcessingResponse:
    task = processing_service.queue_case_for_processing(
        case_id=case_id,
        requested_by=request.actor_id,
    )

    if request.run_synchronously:
        result = processing_service.process_case(task)
        return QueueProcessingResponse(
            case_id=result.case_id,
            status=result.final_status,
            correlation_id=result.correlation_id,
            attempt_number=result.attempt_number,
            processed_document_count=result.processed_document_count,
            validation_finding_count=result.validation_finding_count,
            risk_finding_count=result.risk_finding_count,
            compliance_finding_count=result.compliance_finding_count,
            manual_review_required=result.manual_review_required,
            decision_id=result.decision_id,
        )

    return QueueProcessingResponse(
        case_id=case_id,
        status=CaseStatus.QUEUED_FOR_PROCESSING,
        correlation_id=task.correlation_id,
        attempt_number=task.attempt_number,
    )

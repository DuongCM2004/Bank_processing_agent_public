from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import ProcessingServiceDep
from app.schemas.processing import (
    ExtractionResultCreate,
    ExtractionResultResponse,
    QueueProcessingRequest,
    QueueProcessingResponse,
)
from app.security.rbac import Permission, require_permission

router = APIRouter(tags=["processing"])


@router.post(
    "/cases/{case_id}/processing/queue",
    response_model=QueueProcessingResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_permission(Permission.PROCESSING_QUEUE))],
)
def queue_case_processing(
    case_id: UUID,
    request: QueueProcessingRequest,
    service: ProcessingServiceDep,
) -> QueueProcessingResponse:
    return service.queue_case_processing(case_id=case_id, request=request)


@router.post(
    "/processing/extractions",
    response_model=ExtractionResultResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_extraction_result(
    request: ExtractionResultCreate,
    service: ProcessingServiceDep,
) -> ExtractionResultResponse:
    return service.record_extraction_result(request)


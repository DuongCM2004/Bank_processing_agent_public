from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.api.dependencies import DocumentServiceDep, ManualReviewServiceDep
from app.core.exceptions import ValidationAppError
from app.schemas.documents import (
    DocumentExtractionResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentReviewRequest,
    DocumentReviewResponse,
    DocumentStatusResponse,
    DocumentUploadQueuedResponse,
)
from app.security.rbac import Permission, require_permission

router = APIRouter(prefix="/cases/{case_id}/documents", tags=["documents"])
document_router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.DOCUMENT_UPLOAD))],
)
async def upload_document(
    case_id: UUID,
    service: DocumentServiceDep,
    file: UploadFile = File(...),
    document_type: str = Form(..., max_length=80),
    document_metadata: str = Form(default="{}"),
    actor_id: str | None = Form(default=None, max_length=128),
) -> DocumentResponse:
    try:
        metadata = json.loads(document_metadata)
    except json.JSONDecodeError as exc:
        raise ValidationAppError("document_metadata must be valid JSON.") from exc
    if not isinstance(metadata, dict):
        raise ValidationAppError("document_metadata must be a JSON object.")
    content = await file.read()
    return service.upload_document(
        case_id=case_id,
        filename=file.filename or "document",
        content_type=file.content_type or "application/octet-stream",
        content=content,
        document_type=document_type,
        document_metadata=metadata,
        actor_id=actor_id,
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    dependencies=[Depends(require_permission(Permission.CASE_READ))],
)
def list_documents(case_id: UUID, service: DocumentServiceDep) -> DocumentListResponse:
    return service.list_documents(case_id)


@document_router.post(
    "/upload",
    response_model=DocumentUploadQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_permission(Permission.DOCUMENT_UPLOAD))],
)
async def upload_document_for_extraction(
    service: DocumentServiceDep,
    file: UploadFile = File(...),
    case_id: UUID = Form(...),
    document_type: str = Form(default="identity_document", max_length=80),
    document_metadata: str = Form(default="{}"),
    actor_id: str | None = Form(default=None, max_length=128),
) -> DocumentUploadQueuedResponse:
    try:
        metadata = json.loads(document_metadata)
    except json.JSONDecodeError as exc:
        raise ValidationAppError("document_metadata must be valid JSON.") from exc
    if not isinstance(metadata, dict):
        raise ValidationAppError("document_metadata must be a JSON object.")
    content = await file.read()
    return service.upload_and_queue_document(
        case_id=case_id,
        filename=file.filename or "document",
        content_type=file.content_type or "application/octet-stream",
        content=content,
        document_type=document_type,
        document_metadata=metadata,
        actor_id=actor_id,
    )


@document_router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
    dependencies=[Depends(require_permission(Permission.CASE_READ))],
)
def get_document_status(document_id: UUID, service: DocumentServiceDep) -> DocumentStatusResponse:
    return service.get_document_status(document_id)


@document_router.get(
    "/{document_id}/extraction",
    response_model=DocumentExtractionResponse,
    dependencies=[Depends(require_permission(Permission.CASE_READ))],
)
def get_document_extraction(document_id: UUID, service: DocumentServiceDep) -> DocumentExtractionResponse:
    return service.get_document_extraction(document_id)


@document_router.post(
    "/{document_id}/review",
    response_model=DocumentReviewResponse,
    dependencies=[Depends(require_permission(Permission.MANUAL_REVIEW_CREATE))],
)
def review_document(
    document_id: UUID,
    request: DocumentReviewRequest,
    service: ManualReviewServiceDep,
) -> DocumentReviewResponse:
    return service.review_document(document_id=document_id, request=request)

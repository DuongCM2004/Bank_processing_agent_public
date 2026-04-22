from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from ops_agent.api.dependencies import DocumentAccessServiceDep
from ops_agent.api.openapi import error_responses
from ops_agent.api.schemas import (
    DocumentExtractionResponse,
    DocumentReviewRequest,
    DocumentReviewResponse,
    DocumentStatusResponse,
)
from ops_agent.security.rbac import Permission, require_permission

router = APIRouter(prefix="/documents", tags=["document-extraction"])


@router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get document processing status",
    description="Returns the current document status and the latest extraction run reference for a document.",
    operation_id="getDocumentStatus",
    responses=error_responses(401, 403, 404, 422, 500),
    dependencies=[Depends(require_permission(Permission.DOCUMENT_READ))],
)
def get_document_status(
    document_id: UUID,
    document_service: DocumentAccessServiceDep,
) -> DocumentStatusResponse:
    return document_service.get_document_status(document_id=document_id)


@router.get(
    "/{document_id}/extraction",
    response_model=DocumentExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get document extraction fields",
    description="Returns the latest extracted identity-document fields for manual review.",
    operation_id="getDocumentExtraction",
    responses=error_responses(401, 403, 404, 422, 500),
    dependencies=[Depends(require_permission(Permission.DOCUMENT_READ))],
)
def get_document_extraction(
    document_id: UUID,
    document_service: DocumentAccessServiceDep,
) -> DocumentExtractionResponse:
    return document_service.get_document_extraction(document_id=document_id)


@router.post(
    "/{document_id}/review",
    response_model=DocumentReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Review document extraction",
    description="Saves reviewer edits, approvals, or rejections for the latest extraction result.",
    operation_id="reviewDocumentExtraction",
    responses=error_responses(401, 403, 404, 409, 422, 500),
    dependencies=[Depends(require_permission(Permission.MANUAL_REVIEW_WRITE))],
)
def review_document(
    document_id: UUID,
    request: DocumentReviewRequest,
    document_service: DocumentAccessServiceDep,
) -> DocumentReviewResponse:
    return document_service.review_document(document_id=document_id, request=request)

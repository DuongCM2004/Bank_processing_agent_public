from __future__ import annotations

from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from ops_agent.api.dependencies import DocumentAccessServiceDep, get_extraction_provider
from ops_agent.api.openapi import error_responses
from ops_agent.api.schemas import (
    DocumentExtractionResponse,
    DocumentReviewRequest,
    DocumentReviewResponse,
    DocumentStatusResponse,
    IdentityDocumentExtractionResponse,
)
from ops_agent.domain.shared.exceptions import OpsAgentError
from ops_agent.infrastructure.providers.interfaces import (
    ExtractionProvider,
    ExtractionProviderRequest,
)
from ops_agent.security.rbac import Permission, require_permission

router = APIRouter(prefix="/documents", tags=["document-extraction"])

_PREVIEW_ALLOWED_MIME = {"image/png", "image/jpeg"}
_PREVIEW_MAX_BYTES = 15 * 1024 * 1024


@router.post(
    "/extract-preview",
    response_model=IdentityDocumentExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract identity fields from a staged file without creating a case",
    description=(
        "Runs the configured LLM + LangGraph extraction pipeline on an uploaded image "
        "and returns the identity-document fields. No case, document record, or audit "
        "entry is persisted. Intended for pre-case previews."
    ),
    operation_id="previewDocumentExtraction",
    responses=error_responses(400, 401, 403, 413, 415, 422, 500),
    dependencies=[Depends(require_permission(Permission.DOCUMENT_UPLOAD))],
)
async def preview_document_extraction(
    file: Annotated[UploadFile, File(...)],
    extraction_provider: Annotated[ExtractionProvider, Depends(get_extraction_provider)],
    document_type: Annotated[str, Form()] = "identity_document",
) -> IdentityDocumentExtractionResponse:
    mime_type = (file.content_type or "").lower()
    if mime_type not in _PREVIEW_ALLOWED_MIME:
        raise OpsAgentError(
            f"Preview extraction supports {sorted(_PREVIEW_ALLOWED_MIME)}, got '{mime_type}'.",
            error_code="unsupported_preview_media_type",
            status_code=415,
        )

    content = await file.read()
    if not content:
        raise OpsAgentError(
            "Uploaded file is empty.",
            error_code="empty_preview_upload",
            status_code=400,
        )
    if len(content) > _PREVIEW_MAX_BYTES:
        raise OpsAgentError(
            f"Uploaded file exceeds preview limit of {_PREVIEW_MAX_BYTES} bytes.",
            error_code="preview_upload_too_large",
            status_code=413,
        )

    synthetic_uuid = uuid4()
    request = ExtractionProviderRequest(
        case_id=synthetic_uuid,
        document_id=synthetic_uuid,
        document_type=document_type,
        filename=file.filename or "preview-upload",
        raw_text="",
        mime_type=mime_type,
        content=content,
    )
    try:
        result = extraction_provider.process(request)
    except OpsAgentError:
        raise
    except Exception as exc:
        message = str(exc) or exc.__class__.__name__
        if "invalid_api_key" in message or "Incorrect API key" in message:
            raise OpsAgentError(
                "The configured LLM API key is invalid. Update OPS_AGENT_OPENAI_API_KEY in apps/backend/.env and restart the backend.",
                error_code="llm_invalid_api_key",
                status_code=502,
            ) from exc
        raise OpsAgentError(
            f"Extraction provider failed: {message}",
            error_code="extraction_provider_error",
            status_code=502,
        ) from exc
    payload = result.extracted_payload or {}
    return IdentityDocumentExtractionResponse(
        **{key: payload.get(key) for key in IdentityDocumentExtractionResponse.model_fields}
    )


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

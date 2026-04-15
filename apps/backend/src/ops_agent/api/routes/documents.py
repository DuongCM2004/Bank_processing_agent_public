from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.responses import FileResponse

from ops_agent.api.dependencies import DocumentAccessServiceDep, DocumentUploadServiceDep
from ops_agent.api.schemas import DocumentListResponse, DocumentUploadMetadataResponse, DocumentUploadRequest
from ops_agent.application.services.document_upload import parse_upload_metadata

router = APIRouter(prefix="/cases/{case_id}/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
def list_case_documents(case_id: UUID, document_service: DocumentAccessServiceDep) -> DocumentListResponse:
    return document_service.list_case_documents(case_id=case_id)


@router.post("", response_model=DocumentUploadMetadataResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    case_id: UUID,
    document_service: DocumentUploadServiceDep,
    file: Annotated[UploadFile, File(...)],
    document_type: Annotated[str, Form(...)],
    source_channel: Annotated[str, Form()] = "manual_upload",
    uploaded_by_user_id: Annotated[UUID | None, Form()] = None,
    metadata: Annotated[str | None, Form()] = None,
) -> DocumentUploadMetadataResponse:
    request = DocumentUploadRequest(
        document_type=document_type,
        source_channel=source_channel,
        uploaded_by_user_id=uploaded_by_user_id,
        metadata=parse_upload_metadata(metadata),
    )
    return await document_service.upload_document(case_id=case_id, upload=file, request=request)


@router.get("/{document_id}", response_model=DocumentUploadMetadataResponse)
def get_case_document(
    case_id: UUID,
    document_id: UUID,
    document_service: DocumentAccessServiceDep,
) -> DocumentUploadMetadataResponse:
    return document_service.get_document_metadata(case_id=case_id, document_id=document_id)


@router.get("/{document_id}/download")
def download_case_document(
    case_id: UUID,
    document_id: UUID,
    document_service: DocumentAccessServiceDep,
    downloaded_by_user_id: UUID | None = None,
) -> FileResponse:
    resolved = document_service.prepare_download(
        case_id=case_id,
        document_id=document_id,
        downloaded_by_user_id=downloaded_by_user_id,
    )
    return FileResponse(
        path=resolved.stored_document.absolute_path,
        media_type=resolved.document.mime_type,
        filename=resolved.document.filename,
    )

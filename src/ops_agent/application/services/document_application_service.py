from __future__ import annotations

import hashlib
from datetime import datetime

from ops_agent.models import DocumentCreate, DocumentRecord, DocumentVersionRecord, ProcessingStatus, new_id
from ops_agent.repository import InMemoryRepository


class DocumentApplicationService:
    """Document registration logic stays separate from case orchestration."""

    def __init__(self, repository: InMemoryRepository) -> None:
        self.repository = repository

    def create_document(self, *, case_id: str, request: DocumentCreate, created_at: datetime) -> DocumentRecord:
        file_hash = self._hash(case_id=case_id, filename=request.filename, mime_type=request.mime_type)
        record = DocumentRecord(
            document_id=new_id("doc"),
            case_id=case_id,
            filename=request.filename,
            mime_type=request.mime_type,
            source_channel=request.source_channel,
            retention_class=request.retention_class,
            file_hash=file_hash,
            status=ProcessingStatus.NOT_STARTED,
            created_at=created_at,
        )
        self.repository.save_document(record)
        self.repository.save_document_version(
            DocumentVersionRecord(
                document_version_id=new_id("doc_ver"),
                document_id=record.document_id,
                case_id=case_id,
                version_number=1,
                file_hash=file_hash,
                storage_status="registered",
                created_at=created_at,
            )
        )
        return record

    @staticmethod
    def _hash(*, case_id: str, filename: str, mime_type: str) -> str:
        return hashlib.sha256(f"{case_id}:{filename}:{mime_type}".encode("utf-8")).hexdigest()

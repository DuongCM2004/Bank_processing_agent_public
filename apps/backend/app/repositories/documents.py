from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document, ExtractionResult, OCRResult


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, document: Document) -> Document:
        self.db.add(document)
        return document

    def get(self, document_id: UUID) -> Document | None:
        return self.db.get(Document, document_id)

    def list_by_case(self, case_id: UUID) -> list[Document]:
        return list(self.db.scalars(select(Document).where(Document.case_id == case_id)))


class ProcessingResultRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_ocr_result(self, result: OCRResult) -> OCRResult:
        self.db.add(result)
        return result

    def add_extraction_result(self, result: ExtractionResult) -> ExtractionResult:
        self.db.add(result)
        return result

    def list_extractions_for_case(self, case_id: UUID) -> list[ExtractionResult]:
        stmt = (
            select(ExtractionResult)
            .join(Document, Document.id == ExtractionResult.document_id)
            .where(Document.case_id == case_id)
        )
        return list(self.db.scalars(stmt))

    def list_extractions_for_document(self, document_id: UUID) -> list[ExtractionResult]:
        stmt = (
            select(ExtractionResult)
            .where(ExtractionResult.document_id == document_id)
            .order_by(ExtractionResult.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def get_latest_extraction_for_document(self, document_id: UUID) -> ExtractionResult | None:
        stmt = (
            select(ExtractionResult)
            .where(ExtractionResult.document_id == document_id)
            .order_by(ExtractionResult.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ops_agent.infrastructure.db.models import AuditEvent, Case, Document, ExtractionResult


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_case_by_id(self, case_id: UUID) -> Case | None:
        statement = select(Case).where(Case.id == case_id)
        return self._session.execute(statement).scalar_one_or_none()

    def list_case_documents(self, case_id: UUID) -> list[Document]:
        statement = select(Document).where(Document.case_id == case_id).order_by(Document.created_at.asc())
        return list(self._session.execute(statement).scalars().all())

    def get_document_by_id(self, case_id: UUID, document_id: UUID) -> Document | None:
        statement = select(Document).where(Document.case_id == case_id, Document.id == document_id)
        return self._session.execute(statement).scalar_one_or_none()

    def get_document_by_uuid(self, document_id: UUID) -> Document | None:
        statement = select(Document).where(Document.id == document_id)
        return self._session.execute(statement).scalar_one_or_none()

    def get_latest_extraction_result(self, document_id: UUID) -> ExtractionResult | None:
        statement = (
            select(ExtractionResult)
            .where(ExtractionResult.document_id == document_id)
            .order_by(ExtractionResult.created_at.desc())
            .limit(1)
        )
        return self._session.execute(statement).scalar_one_or_none()

    def add_document(self, document: Document) -> Document:
        self._session.add(document)
        return document

    def add_audit_event(self, audit_event: AuditEvent) -> AuditEvent:
        self._session.add(audit_event)
        return audit_event

    def flush(self) -> None:
        self._session.flush()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def refresh(self, entity: object) -> None:
        self._session.refresh(entity)

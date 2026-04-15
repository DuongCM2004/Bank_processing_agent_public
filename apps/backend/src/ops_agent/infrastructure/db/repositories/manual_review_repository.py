from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ops_agent.infrastructure.db.models import AuditEvent, Case, Decision, Document, ExtractionResult, ManualReviewAction


class ManualReviewRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_case_by_id(self, case_id: UUID) -> Case | None:
        statement = (
            select(Case)
            .where(Case.id == case_id)
            .options(
                selectinload(Case.documents),
                selectinload(Case.decisions),
                selectinload(Case.manual_review_actions),
            )
        )
        return self._session.execute(statement).scalar_one_or_none()

    def get_document_by_id(self, case_id: UUID, document_id: UUID) -> Document | None:
        statement = select(Document).where(Document.case_id == case_id, Document.id == document_id)
        return self._session.execute(statement).scalar_one_or_none()

    def get_extraction_result_by_id(self, case_id: UUID, extraction_result_id: UUID) -> ExtractionResult | None:
        statement = (
            select(ExtractionResult)
            .join(Document, ExtractionResult.document_id == Document.id)
            .where(Document.case_id == case_id, ExtractionResult.id == extraction_result_id)
        )
        return self._session.execute(statement).scalar_one_or_none()

    def get_decision_by_id(self, case_id: UUID, decision_id: UUID) -> Decision | None:
        statement = select(Decision).where(Decision.case_id == case_id, Decision.id == decision_id)
        return self._session.execute(statement).scalar_one_or_none()

    def add_manual_review_action(self, action: ManualReviewAction) -> ManualReviewAction:
        self._session.add(action)
        return action

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

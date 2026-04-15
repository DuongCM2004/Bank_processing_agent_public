from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ops_agent.domain.shared.enums import CaseStatus
from ops_agent.infrastructure.db.models import (
    AuditEvent,
    Case,
    ComplianceFinding,
    Decision,
    Document,
    ExtractionResult,
    ManualReviewAction,
    OCRResult,
    RiskFinding,
    User,
    ValidationFinding,
)


@dataclass(slots=True)
class CaseListFilters:
    status: CaseStatus | None = None
    current_queue: str | None = None
    case_type: str | None = None


class CaseRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, case: Case) -> Case:
        self._session.add(case)
        return case

    def add_audit_event(self, audit_event: AuditEvent) -> AuditEvent:
        self._session.add(audit_event)
        return audit_event

    def get_by_id(self, case_id: UUID) -> Case | None:
        statement = (
            select(Case)
            .where(Case.id == case_id)
            .options(selectinload(Case.documents), selectinload(Case.submitted_by_user).selectinload(User.roles))
        )
        return self._session.execute(statement).scalar_one_or_none()

    def get_detail_by_id(self, case_id: UUID) -> Case | None:
        statement = (
            select(Case)
            .where(Case.id == case_id)
            .options(
                selectinload(Case.submitted_by_user).selectinload(User.roles),
                selectinload(Case.documents).selectinload(Document.ocr_results),
                selectinload(Case.documents).selectinload(Document.extraction_results),
                selectinload(Case.validation_findings),
                selectinload(Case.risk_findings),
                selectinload(Case.compliance_findings),
                selectinload(Case.decisions),
                selectinload(Case.manual_review_actions),
                selectinload(Case.audit_events),
            )
        )
        return self._session.execute(statement).scalar_one_or_none()

    def list_cases(self, *, filters: CaseListFilters, limit: int, offset: int) -> tuple[list[Case], int]:
        statement = select(Case).options(selectinload(Case.documents)).order_by(Case.created_at.desc())
        count_statement = select(func.count()).select_from(Case)

        if filters.status is not None:
            statement = statement.where(Case.status == filters.status)
            count_statement = count_statement.where(Case.status == filters.status)
        if filters.current_queue:
            statement = statement.where(Case.current_queue == filters.current_queue)
            count_statement = count_statement.where(Case.current_queue == filters.current_queue)
        if filters.case_type:
            statement = statement.where(Case.case_type == filters.case_type)
            count_statement = count_statement.where(Case.case_type == filters.case_type)

        statement = statement.limit(limit).offset(offset)
        items = list(self._session.execute(statement).scalars().all())
        total = int(self._session.execute(count_statement).scalar_one())
        return items, total

    def flush(self) -> None:
        self._session.flush()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def refresh(self, entity: object) -> None:
        self._session.refresh(entity)

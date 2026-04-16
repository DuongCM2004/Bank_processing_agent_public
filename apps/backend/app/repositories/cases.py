from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.case import Case
from app.models.enums import CaseStatus


class CaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, case: Case) -> Case:
        self.db.add(case)
        return case

    def get(self, case_id: UUID) -> Case | None:
        return self.db.get(Case, case_id)

    def get_detail(self, case_id: UUID) -> Case | None:
        stmt = (
            select(Case)
            .where(Case.id == case_id)
            .options(
                selectinload(Case.documents),
                selectinload(Case.decisions),
                selectinload(Case.manual_review_actions),
                selectinload(Case.audit_events),
            )
        )
        return self.db.scalar(stmt)

    def get_by_reference(self, case_reference: str) -> Case | None:
        return self.db.scalar(select(Case).where(Case.case_reference == case_reference))

    def list(
        self,
        *,
        limit: int,
        offset: int,
        status: CaseStatus | None = None,
        current_queue: str | None = None,
        case_type: str | None = None,
    ) -> tuple[list[Case], int]:
        stmt: Select[tuple[Case]] = select(Case)
        count_stmt = select(func.count()).select_from(Case)
        filters = []
        if status is not None:
            filters.append(Case.status == status)
        if current_queue is not None:
            filters.append(Case.current_queue == current_queue)
        if case_type is not None:
            filters.append(Case.case_type == case_type)
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total = self.db.scalar(count_stmt) or 0
        items = list(self.db.scalars(stmt.order_by(Case.created_at.desc()).limit(limit).offset(offset)))
        return items, total


from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.decision import Decision


class DecisionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, decision: Decision) -> Decision:
        self.db.add(decision)
        return decision

    def list_for_case(self, case_id: UUID) -> list[Decision]:
        return list(self.db.scalars(select(Decision).where(Decision.case_id == case_id)))


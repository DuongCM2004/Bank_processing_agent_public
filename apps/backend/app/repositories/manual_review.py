from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.manual_review import ManualReviewAction


class ManualReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, action: ManualReviewAction) -> ManualReviewAction:
        self.db.add(action)
        return action

    def list_for_case(self, case_id: UUID) -> list[ManualReviewAction]:
        return list(self.db.scalars(select(ManualReviewAction).where(ManualReviewAction.case_id == case_id)))


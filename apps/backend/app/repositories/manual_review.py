from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ManualReviewActionType
from app.models.manual_review import ManualReviewAction


class ManualReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, action: ManualReviewAction) -> ManualReviewAction:
        self.db.add(action)
        return action

    def list_for_case(self, case_id: UUID) -> list[ManualReviewAction]:
        return list(self.db.scalars(select(ManualReviewAction).where(ManualReviewAction.case_id == case_id)))

    def get_latest_for_document(
        self,
        document_id: UUID,
        *,
        action_types: set[ManualReviewActionType] | None = None,
    ) -> ManualReviewAction | None:
        stmt = select(ManualReviewAction).where(ManualReviewAction.document_id == document_id)
        if action_types:
            stmt = stmt.where(ManualReviewAction.action_type.in_(action_types))
        stmt = stmt.order_by(ManualReviewAction.created_at.desc()).limit(1)
        return self.db.scalar(stmt)

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedModel
from app.models.enums import ManualReviewActionType

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.document import Document


class ManualReviewAction(TimestampedModel):
    __tablename__ = "manual_review_actions"

    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"))
    document_id: Mapped[UUID | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    action_type: Mapped[ManualReviewActionType] = mapped_column(
        Enum(ManualReviewActionType, native_enum=False)
    )
    reviewer_id: Mapped[str] = mapped_column(String(128), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    evidence_refs: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False, default=list)

    case: Mapped["Case"] = relationship(back_populates="manual_review_actions")
    document: Mapped["Document | None"] = relationship(back_populates="manual_review_actions")


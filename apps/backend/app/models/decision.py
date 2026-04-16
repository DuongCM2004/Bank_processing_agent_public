from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedModel
from app.models.enums import DecisionOutcome

if TYPE_CHECKING:
    from app.models.case import Case


class Decision(TimestampedModel):
    __tablename__ = "decisions"

    case_id: Mapped[UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"))
    outcome: Mapped[DecisionOutcome] = mapped_column(Enum(DecisionOutcome, native_enum=False))
    decided_by: Mapped[str] = mapped_column(String(128), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_refs: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False, default=list)
    decision_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    case: Mapped["Case"] = relationship(back_populates="decisions")


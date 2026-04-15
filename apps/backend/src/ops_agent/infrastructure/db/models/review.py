from __future__ import annotations

from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ops_agent.domain.shared.enums import DecisionOutcome, DecisionType, ManualReviewActionType
from ops_agent.infrastructure.db.models.base import BaseModel, future_info, mvp_info


class Decision(BaseModel):
    __tablename__ = "decisions"
    __table_args__ = (Index("ix_decisions_case_id", "case_id"),)

    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        info=mvp_info("Owning case for the decision."),
    )
    decided_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        info=mvp_info("Reviewer or supervisor that issued the decision when human-originated."),
    )
    decision_type: Mapped[DecisionType] = mapped_column(
        Enum(DecisionType, native_enum=False),
        nullable=False,
        info=mvp_info("Decision source category for auditability."),
    )
    outcome: Mapped[DecisionOutcome] = mapped_column(
        Enum(DecisionOutcome, native_enum=False),
        nullable=False,
        info=mvp_info("Explicit decision outcome."),
    )
    reason_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        info=mvp_info("Decision rationale code for reporting and traceability."),
    )
    rationale: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        info=mvp_info("Human-readable decision explanation."),
    )
    confidence_score: Mapped[float | None] = mapped_column(
        nullable=True,
        info=future_info("Model confidence or reviewer certainty score."),
    )
    evidence_refs: Mapped[list[dict[str, object]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        info=mvp_info("Evidence pointers supporting the decision."),
    )
    linked_findings: Mapped[list[dict[str, object]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        info=mvp_info("Referenced case findings that informed the decision outcome."),
    )
    supersedes_decision_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("decisions.id", ondelete="SET NULL"),
        nullable=True,
        info=future_info("Previous decision replaced by this record."),
    )

    case: Mapped["Case"] = relationship(back_populates="decisions")
    decided_by_user: Mapped["User | None"] = relationship(back_populates="decisions")
    manual_review_actions: Mapped[list["ManualReviewAction"]] = relationship(back_populates="related_decision")
    supersedes_decision: Mapped["Decision | None"] = relationship(remote_side="Decision.id")


class ManualReviewAction(BaseModel):
    __tablename__ = "manual_review_actions"
    __table_args__ = (Index("ix_manual_review_actions_case_id", "case_id"),)

    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        info=mvp_info("Owning case for the manual review event."),
    )
    document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        info=mvp_info("Optional document directly affected by the review action."),
    )
    performed_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        info=mvp_info("Operations user that performed the manual action."),
    )
    related_decision_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("decisions.id", ondelete="SET NULL"),
        nullable=True,
        info=future_info("Decision record created or modified by this action."),
    )
    action_type: Mapped[ManualReviewActionType] = mapped_column(
        Enum(ManualReviewActionType, native_enum=False),
        nullable=False,
        info=mvp_info("Explicit action type recorded during review."),
    )
    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        info=mvp_info("Operator note explaining the action."),
    )
    payload: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        info=mvp_info("Structured action payload such as corrected fields."),
    )
    evidence_refs: Mapped[list[dict[str, object]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        info=mvp_info("Evidence pointers referenced during the manual action."),
    )

    case: Mapped["Case"] = relationship(back_populates="manual_review_actions")
    document: Mapped["Document | None"] = relationship(back_populates="manual_review_actions")
    performed_by_user: Mapped["User"] = relationship(back_populates="manual_review_actions")
    related_decision: Mapped["Decision | None"] = relationship(back_populates="manual_review_actions")

"""Align schema with locked app package MVP models.

Revision ID: 20260416_0002
Revises: 20260415_0001
Create Date: 2026-04-16 21:45:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260416_0002"
down_revision = "20260415_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("decisions", sa.Column("decided_by", sa.String(length=128), nullable=True))
    op.add_column("decisions", sa.Column("decision_metadata", sa.JSON(), nullable=True))
    op.alter_column("decisions", "decision_type", existing_type=sa.String(length=25), nullable=True)
    op.alter_column("decisions", "reason_code", existing_type=sa.String(length=100), nullable=True)
    op.alter_column("decisions", "linked_findings", existing_type=sa.JSON(), nullable=True)

    op.add_column("manual_review_actions", sa.Column("reviewer_id", sa.String(length=128), nullable=True))
    op.alter_column(
        "manual_review_actions",
        "performed_by_user_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )

    op.add_column("audit_events", sa.Column("actor_id", sa.String(length=128), nullable=True))
    op.add_column("audit_events", sa.Column("entity_type", sa.String(length=80), nullable=True))
    op.add_column("audit_events", sa.Column("entity_id", sa.String(length=80), nullable=True))
    op.add_column("audit_events", sa.Column("message", sa.String(length=255), nullable=True))
    op.alter_column("audit_events", "summary", existing_type=sa.String(length=255), nullable=True)
    op.alter_column("audit_events", "resource_type", existing_type=sa.String(length=80), nullable=True)
    op.alter_column("audit_events", "resource_id", existing_type=sa.Uuid(), nullable=True)
    op.alter_column("audit_events", "evidence_refs", existing_type=sa.JSON(), nullable=True)


def downgrade() -> None:
    op.alter_column("audit_events", "evidence_refs", existing_type=sa.JSON(), nullable=False)
    op.alter_column("audit_events", "resource_id", existing_type=sa.Uuid(), nullable=False)
    op.alter_column("audit_events", "resource_type", existing_type=sa.String(length=80), nullable=False)
    op.alter_column("audit_events", "summary", existing_type=sa.String(length=255), nullable=False)
    op.drop_column("audit_events", "message")
    op.drop_column("audit_events", "entity_id")
    op.drop_column("audit_events", "entity_type")
    op.drop_column("audit_events", "actor_id")

    op.alter_column(
        "manual_review_actions",
        "performed_by_user_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
    op.drop_column("manual_review_actions", "reviewer_id")

    op.alter_column("decisions", "linked_findings", existing_type=sa.JSON(), nullable=False)
    op.alter_column("decisions", "reason_code", existing_type=sa.String(length=100), nullable=False)
    op.alter_column("decisions", "decision_type", existing_type=sa.String(length=25), nullable=False)
    op.drop_column("decisions", "decision_metadata")
    op.drop_column("decisions", "decided_by")


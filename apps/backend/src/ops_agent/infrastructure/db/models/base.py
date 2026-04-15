from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ops_agent.infrastructure.db.base import Base, TimestampedModel


def mvp_info(note: str) -> dict[str, Any]:
    return {"delivery_phase": "mvp_required", "note": note}


def future_info(note: str) -> dict[str, Any]:
    return {"delivery_phase": "future", "note": note}


class BaseModel(Base, TimestampedModel):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        info=mvp_info("Stable surrogate key for traceability and joins."),
    )
    created_by: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        info=mvp_info("Actor identifier recorded when the row is created."),
    )
    updated_by: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        info=mvp_info("Actor identifier recorded when the row is last updated."),
    )

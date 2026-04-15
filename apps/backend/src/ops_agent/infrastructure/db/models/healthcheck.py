from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ops_agent.infrastructure.db.models.base import BaseModel


class HealthcheckProbe(BaseModel):
    __tablename__ = "healthcheck_probes"

    probe_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ok")


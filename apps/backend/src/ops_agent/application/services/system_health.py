from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ops_agent.config import AppSettings


class SystemHealthService:
    """Coordinates lightweight readiness checks for runtime dependencies."""

    def __init__(self, settings: AppSettings, session: Session) -> None:
        self._settings = settings
        self._session = session

    def get_health_status(self) -> tuple[str, dict[str, str]]:
        checks = {"api": "ok"}

        if self._settings.features.enable_db_healthcheck:
            checks["database"] = self._check_database()
        else:
            checks["database"] = "skipped"

        overall_status = "ok" if all(value in {"ok", "skipped"} for value in checks.values()) else "degraded"
        return overall_status, checks

    def _check_database(self) -> str:
        try:
            self._session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return "unavailable"
        return "ok"


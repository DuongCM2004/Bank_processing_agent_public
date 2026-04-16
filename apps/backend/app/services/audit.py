from __future__ import annotations

from uuid import UUID

from app.repositories.audit import AuditEventRepository
from app.schemas.audit import AuditEventListResponse, AuditEventResponse


class AuditService:
    def __init__(self, repository: AuditEventRepository) -> None:
        self.repository = repository

    def list_case_events(self, case_id: UUID, *, limit: int, offset: int) -> AuditEventListResponse:
        items, total = self.repository.list_for_case(case_id, limit=limit, offset=offset)
        return AuditEventListResponse(
            items=[AuditEventResponse.model_validate(item) for item in items],
            total=total,
        )


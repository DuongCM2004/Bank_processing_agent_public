from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.audit.logger import AuditLogger
from app.core.exceptions import ConflictError, NotFoundError
from app.models.case import Case
from app.models.enums import AuditActorType, AuditEventType, CaseStatus
from app.repositories.cases import CaseRepository
from app.schemas.cases import (
    CaseCreateRequest,
    CaseListResponse,
    CaseResponse,
    CaseStatusTransitionRequest,
    CaseStatusTransitionResponse,
)
from app.workflows.case_state import CaseTransitionContext, CaseWorkflowStateMachine


class CaseService:
    def __init__(self, repository: CaseRepository, audit_logger: AuditLogger) -> None:
        self.repository = repository
        self.audit_logger = audit_logger
        self.state_machine = CaseWorkflowStateMachine.default()

    def create_case(self, request: CaseCreateRequest) -> CaseResponse:
        now = datetime.now(UTC)
        case = Case(
            case_reference=request.case_reference,
            case_type=request.case_type,
            status=CaseStatus.CREATED,
            status_changed_at=now,
            current_queue=request.current_queue,
            source_channel=request.source_channel,
            customer_reference=request.customer_reference,
            case_metadata=request.case_metadata,
            created_by=request.actor_id,
            updated_by=request.actor_id,
        )
        self.repository.add(case)
        self.repository.db.flush()
        self.audit_logger.record(
            event_type=AuditEventType.CASE_CREATED,
            actor_type=AuditActorType.USER,
            actor_id=request.actor_id,
            case_id=case.id,
            entity_type="case",
            entity_id=case.id,
            message="Case created.",
            details={"case_reference": request.case_reference, "case_type": request.case_type},
        )
        try:
            self.repository.db.commit()
        except IntegrityError as exc:
            self.repository.db.rollback()
            raise ConflictError("Case reference already exists.", error_code="case_reference_exists") from exc
        self.repository.db.refresh(case)
        return CaseResponse.model_validate(case)

    def get_case(self, case_id: UUID) -> Case:
        case = self.repository.get(case_id)
        if case is None:
            raise NotFoundError("Case not found.", error_code="case_not_found")
        return case

    def list_cases(
        self,
        *,
        limit: int,
        offset: int,
        status: CaseStatus | None,
        current_queue: str | None,
        case_type: str | None,
    ) -> CaseListResponse:
        items, total = self.repository.list(
            limit=limit,
            offset=offset,
            status=status,
            current_queue=current_queue,
            case_type=case_type,
        )
        return CaseListResponse(
            items=[CaseResponse.model_validate(case) for case in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    def transition_case(
        self,
        *,
        case_id: UUID,
        request: CaseStatusTransitionRequest,
    ) -> CaseStatusTransitionResponse:
        case = self.get_case(case_id)
        previous_status = case.status
        rule = self.state_machine.validate(
            case_id=case.id,
            from_status=case.status,
            to_status=request.to_status,
        )
        context = CaseTransitionContext(
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            reason_code=request.reason_code,
            comment=request.comment,
            metadata=request.metadata,
        )
        case.status = request.to_status
        case.status_changed_at = context.occurred_at
        case.updated_at = context.occurred_at
        case.updated_by = request.actor_id
        self.audit_logger.record(
            event_type=AuditEventType.STATUS_CHANGED,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            case_id=case.id,
            entity_type="case",
            entity_id=case.id,
            message=f"Case status changed from {previous_status.value} to {request.to_status.value}.",
            details={
                "from_status": previous_status.value,
                "to_status": request.to_status.value,
                "transition_name": rule.transition_name,
                "reason_code": request.reason_code or rule.reason_code,
                "comment": request.comment,
                "metadata": request.metadata,
            },
        )
        self.repository.db.commit()
        self.repository.db.refresh(case)
        return CaseStatusTransitionResponse(
            case_id=case.id,
            from_status=previous_status,
            to_status=case.status,
            transition_name=rule.transition_name,
            status_changed_at=case.status_changed_at,
        )

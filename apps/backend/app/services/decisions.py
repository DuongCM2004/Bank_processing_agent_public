from __future__ import annotations

from uuid import UUID

from app.audit.logger import AuditLogger
from app.core.exceptions import NotFoundError
from app.models.decision import Decision
from app.models.enums import AuditActorType, AuditEventType, CaseStatus, DecisionOutcome
from app.repositories.cases import CaseRepository
from app.repositories.decisions import DecisionRepository
from app.schemas.cases import CaseStatusTransitionRequest
from app.schemas.decisions import DecisionCreateRequest, DecisionResponse
from app.services.cases import CaseService


class DecisionService:
    def __init__(
        self,
        decision_repository: DecisionRepository,
        case_repository: CaseRepository,
        case_service: CaseService,
        audit_logger: AuditLogger,
    ) -> None:
        self.decision_repository = decision_repository
        self.case_repository = case_repository
        self.case_service = case_service
        self.audit_logger = audit_logger

    def create_decision(self, *, case_id: UUID, request: DecisionCreateRequest) -> DecisionResponse:
        case = self.case_repository.get(case_id)
        if case is None:
            raise NotFoundError("Case not found.", error_code="case_not_found")
        decision = Decision(
            case_id=case_id,
            outcome=request.outcome,
            decided_by=request.actor_id,
            rationale=request.rationale,
            evidence_refs=[item.model_dump(mode="json") for item in request.evidence_refs],
            decision_metadata=request.decision_metadata,
            created_by=request.actor_id,
            updated_by=request.actor_id,
        )
        self.decision_repository.add(decision)
        self.decision_repository.db.flush()
        self.audit_logger.record(
            event_type=AuditEventType.DECISION_RECORDED,
            actor_type=AuditActorType.USER,
            actor_id=request.actor_id,
            case_id=case_id,
            entity_type="decision",
            entity_id=decision.id,
            message="Decision recorded.",
            details={"outcome": request.outcome.value},
        )
        self.decision_repository.db.commit()
        self.decision_repository.db.refresh(decision)

        if request.outcome == DecisionOutcome.APPROVED and case.status == CaseStatus.DECISION_READY:
            self.case_service.transition_case(
                case_id=case_id,
                request=CaseStatusTransitionRequest(
                    to_status=CaseStatus.APPROVED,
                    actor_id=request.actor_id,
                    reason_code="case_approved",
                ),
            )
        elif request.outcome == DecisionOutcome.REJECTED and case.status == CaseStatus.DECISION_READY:
            self.case_service.transition_case(
                case_id=case_id,
                request=CaseStatusTransitionRequest(
                    to_status=CaseStatus.REJECTED,
                    actor_id=request.actor_id,
                    reason_code="case_rejected",
                ),
            )
        return DecisionResponse.model_validate(decision)

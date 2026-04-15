from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from ops_agent.api.schemas import (
    DecisionActionRequest,
    DecisionCreateRequest,
    DecisionFindingLinkResponse,
    DecisionResponse,
    DecisionWorkflowResponse,
    EvidenceReferenceResponse,
)
from ops_agent.application.services.audit import AuditService
from ops_agent.application.services.case_workflow import CaseWorkflowService
from ops_agent.domain.shared.enums import (
    AuditActorType,
    CaseStatus,
    DecisionOutcome,
)
from ops_agent.domain.shared.exceptions import ConflictError, ResourceNotFoundError
from ops_agent.domain.workflow import CaseTransitionContext
from ops_agent.infrastructure.db.models import Decision
from ops_agent.infrastructure.db.repositories.decision_repository import DecisionRepository


class DecisionService:
    def __init__(
        self,
        *,
        repository: DecisionRepository,
        workflow_service: CaseWorkflowService,
        audit_service: AuditService,
    ) -> None:
        self._repository = repository
        self._workflow_service = workflow_service
        self._audit_service = audit_service

    def create_decision(self, *, case_id: UUID, request: DecisionCreateRequest) -> DecisionWorkflowResponse:
        return self._create_and_apply_decision(case_id=case_id, request=request)

    def approve_case(self, *, case_id: UUID, request: DecisionActionRequest) -> DecisionWorkflowResponse:
        return self._create_and_apply_decision(
            case_id=case_id,
            request=DecisionCreateRequest(
                decided_by_user_id=request.decided_by_user_id,
                decision_type=request.decision_type,
                outcome=DecisionOutcome.APPROVED,
                reason_code=request.reason_code,
                rationale=request.rationale,
                confidence_score=request.confidence_score,
                evidence_refs=request.evidence_refs,
                linked_findings=request.linked_findings,
                supersedes_decision_id=request.supersedes_decision_id,
            ),
        )

    def reject_case(self, *, case_id: UUID, request: DecisionActionRequest) -> DecisionWorkflowResponse:
        return self._create_and_apply_decision(
            case_id=case_id,
            request=DecisionCreateRequest(
                decided_by_user_id=request.decided_by_user_id,
                decision_type=request.decision_type,
                outcome=DecisionOutcome.REJECTED,
                reason_code=request.reason_code,
                rationale=request.rationale,
                confidence_score=request.confidence_score,
                evidence_refs=request.evidence_refs,
                linked_findings=request.linked_findings,
                supersedes_decision_id=request.supersedes_decision_id,
            ),
        )

    def request_more_review(self, *, case_id: UUID, request: DecisionActionRequest) -> DecisionWorkflowResponse:
        return self._create_and_apply_decision(
            case_id=case_id,
            request=DecisionCreateRequest(
                decided_by_user_id=request.decided_by_user_id,
                decision_type=request.decision_type,
                outcome=DecisionOutcome.REVIEW_REQUIRED,
                reason_code=request.reason_code,
                rationale=request.rationale,
                confidence_score=request.confidence_score,
                evidence_refs=request.evidence_refs,
                linked_findings=request.linked_findings,
                supersedes_decision_id=request.supersedes_decision_id,
            ),
        )

    def _create_and_apply_decision(self, *, case_id: UUID, request: DecisionCreateRequest) -> DecisionWorkflowResponse:
        case = self._get_case(case_id)
        occurred_at = datetime.now(UTC)
        self._validate_case_status(case_status=case.status, outcome=request.outcome)
        linked_findings = self._resolve_linked_findings(case_id=case_id, requested_findings=request.linked_findings)
        evidence_refs = [ref.model_dump(mode="json") for ref in request.evidence_refs]

        if request.supersedes_decision_id is not None:
            prior_decision = self._repository.get_decision_by_id(case_id, request.supersedes_decision_id)
            if prior_decision is None:
                raise ResourceNotFoundError("Decision", str(request.supersedes_decision_id))

        decision = Decision(
            case_id=case.id,
            decided_by_user_id=request.decided_by_user_id,
            decision_type=request.decision_type,
            outcome=request.outcome,
            reason_code=request.reason_code,
            rationale=request.rationale,
            confidence_score=request.confidence_score,
            evidence_refs=evidence_refs,
            linked_findings=linked_findings,
            supersedes_decision_id=request.supersedes_decision_id,
            created_by=str(request.decided_by_user_id),
            updated_by=str(request.decided_by_user_id),
        )
        self._repository.add_decision(decision)
        self._repository.flush()

        target_status = self._target_status_for_outcome(request.outcome)
        self._workflow_service.transition(
            case=case,
            to_status=target_status,
            context=CaseTransitionContext(
                actor_type=AuditActorType.USER,
                actor_id=str(request.decided_by_user_id),
                reason_code=request.reason_code,
                comment=request.rationale,
                metadata={
                    "decision_id": str(decision.id),
                    "decision_outcome": request.outcome.value,
                    "linked_finding_count": len(linked_findings),
                },
                occurred_at=occurred_at,
            ),
        )
        if target_status in {CaseStatus.APPROVED, CaseStatus.REJECTED}:
            case.closed_at = occurred_at

        self._audit_service.record_decision(
            case_id=case.id,
            decision_id=decision.id,
            decided_by_user_id=request.decided_by_user_id,
            decision_type=request.decision_type,
            outcome=request.outcome.value,
            reason_code=request.reason_code,
            linked_findings=linked_findings,
            evidence_refs=evidence_refs,
            occurred_at=occurred_at,
        )
        self._repository.commit()
        self._repository.refresh(case)
        self._repository.refresh(decision)
        return DecisionWorkflowResponse(
            case_id=case.id,
            case_status=case.status,
            status_changed_at=case.status_changed_at,
            decision=self._to_decision_response(decision),
            allowed_next_statuses=list(self._workflow_service.allowed_targets(case.status)),
        )

    def _get_case(self, case_id: UUID):
        case = self._repository.get_case_by_id(case_id)
        if case is None:
            raise ResourceNotFoundError("Case", str(case_id))
        return case

    @staticmethod
    def _validate_case_status(*, case_status: CaseStatus, outcome: DecisionOutcome) -> None:
        if outcome in {DecisionOutcome.APPROVED, DecisionOutcome.REJECTED, DecisionOutcome.REVIEW_REQUIRED}:
            if case_status != CaseStatus.DECISION_READY:
                raise ConflictError(
                    f"Cannot record decision outcome '{outcome.value}' while case is in status '{case_status.value}'.",
                    error_code="decision_not_allowed_for_case_status",
                )
            return
        raise ConflictError(
            f"Decision outcome '{outcome.value}' is not supported in the MVP decision service.",
            error_code="unsupported_decision_outcome",
        )

    def _resolve_linked_findings(self, *, case_id: UUID, requested_findings) -> list[dict[str, object]]:
        resolved: list[dict[str, object]] = []
        for finding in requested_findings:
            finding_type = finding.finding_type.lower()
            if finding_type == "validation":
                finding_record = self._repository.get_validation_finding_by_id(case_id, finding.finding_id)
            elif finding_type == "risk":
                finding_record = self._repository.get_risk_finding_by_id(case_id, finding.finding_id)
            elif finding_type == "compliance":
                finding_record = self._repository.get_compliance_finding_by_id(case_id, finding.finding_id)
            else:
                raise ConflictError(
                    f"Unsupported finding type '{finding.finding_type}'.",
                    error_code="unsupported_decision_finding_type",
                )
            if finding_record is None:
                raise ResourceNotFoundError("Finding", str(finding.finding_id))
            resolved.append({"finding_type": finding_type, "finding_id": str(finding.finding_id)})
        return resolved

    @staticmethod
    def _target_status_for_outcome(outcome: DecisionOutcome) -> CaseStatus:
        if outcome == DecisionOutcome.APPROVED:
            return CaseStatus.APPROVED
        if outcome == DecisionOutcome.REJECTED:
            return CaseStatus.REJECTED
        return CaseStatus.MANUAL_REVIEW_REQUIRED

    @staticmethod
    def _to_decision_response(decision: Decision) -> DecisionResponse:
        return DecisionResponse(
            id=decision.id,
            case_id=decision.case_id,
            decided_by_user_id=decision.decided_by_user_id,
            decision_type=decision.decision_type,
            outcome=decision.outcome,
            reason_code=decision.reason_code,
            rationale=decision.rationale,
            confidence_score=decision.confidence_score,
            evidence_refs=[EvidenceReferenceResponse.model_validate(ref) for ref in decision.evidence_refs],
            linked_findings=[DecisionFindingLinkResponse.model_validate(link) for link in decision.linked_findings],
            supersedes_decision_id=decision.supersedes_decision_id,
            created_at=decision.created_at,
            updated_at=decision.updated_at,
        )

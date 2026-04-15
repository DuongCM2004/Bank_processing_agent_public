from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ops_agent.infrastructure.db.models import (
    AuditEvent,
    Case,
    ComplianceFinding,
    Decision,
    RiskFinding,
    ValidationFinding,
)


class DecisionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_case_by_id(self, case_id: UUID) -> Case | None:
        statement = (
            select(Case)
            .where(Case.id == case_id)
            .options(
                selectinload(Case.decisions),
                selectinload(Case.validation_findings),
                selectinload(Case.risk_findings),
                selectinload(Case.compliance_findings),
            )
        )
        return self._session.execute(statement).scalar_one_or_none()

    def get_decision_by_id(self, case_id: UUID, decision_id: UUID) -> Decision | None:
        statement = select(Decision).where(Decision.case_id == case_id, Decision.id == decision_id)
        return self._session.execute(statement).scalar_one_or_none()

    def get_validation_finding_by_id(self, case_id: UUID, finding_id: UUID) -> ValidationFinding | None:
        statement = select(ValidationFinding).where(ValidationFinding.case_id == case_id, ValidationFinding.id == finding_id)
        return self._session.execute(statement).scalar_one_or_none()

    def get_risk_finding_by_id(self, case_id: UUID, finding_id: UUID) -> RiskFinding | None:
        statement = select(RiskFinding).where(RiskFinding.case_id == case_id, RiskFinding.id == finding_id)
        return self._session.execute(statement).scalar_one_or_none()

    def get_compliance_finding_by_id(self, case_id: UUID, finding_id: UUID) -> ComplianceFinding | None:
        statement = select(ComplianceFinding).where(ComplianceFinding.case_id == case_id, ComplianceFinding.id == finding_id)
        return self._session.execute(statement).scalar_one_or_none()

    def add_decision(self, decision: Decision) -> Decision:
        self._session.add(decision)
        return decision

    def add_audit_event(self, audit_event: AuditEvent) -> AuditEvent:
        self._session.add(audit_event)
        return audit_event

    def flush(self) -> None:
        self._session.flush()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def refresh(self, entity: object) -> None:
        self._session.refresh(entity)

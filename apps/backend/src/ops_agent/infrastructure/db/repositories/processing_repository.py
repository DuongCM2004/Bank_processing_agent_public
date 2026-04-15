from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ops_agent.infrastructure.db.models import (
    AuditEvent,
    Case,
    ComplianceFinding,
    Decision,
    ExtractionResult,
    OCRResult,
    RiskFinding,
    ValidationFinding,
)


class ProcessingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_case_for_processing(self, case_id: UUID) -> Case | None:
        statement = (
            select(Case)
            .where(Case.id == case_id)
            .options(
                selectinload(Case.documents),
                selectinload(Case.validation_findings),
                selectinload(Case.risk_findings),
                selectinload(Case.compliance_findings),
                selectinload(Case.decisions),
            )
        )
        return self._session.execute(statement).scalar_one_or_none()

    def add_audit_event(self, audit_event: AuditEvent) -> AuditEvent:
        self._session.add(audit_event)
        return audit_event

    def add_ocr_result(self, ocr_result: OCRResult) -> OCRResult:
        self._session.add(ocr_result)
        return ocr_result

    def add_extraction_result(self, extraction_result: ExtractionResult) -> ExtractionResult:
        self._session.add(extraction_result)
        return extraction_result

    def add_validation_finding(self, finding: ValidationFinding) -> ValidationFinding:
        self._session.add(finding)
        return finding

    def add_risk_finding(self, finding: RiskFinding) -> RiskFinding:
        self._session.add(finding)
        return finding

    def add_compliance_finding(self, finding: ComplianceFinding) -> ComplianceFinding:
        self._session.add(finding)
        return finding

    def add_decision(self, decision: Decision) -> Decision:
        self._session.add(decision)
        return decision

    def flush(self) -> None:
        self._session.flush()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def refresh(self, entity: object) -> None:
        self._session.refresh(entity)

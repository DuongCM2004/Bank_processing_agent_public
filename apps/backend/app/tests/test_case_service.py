from __future__ import annotations

from sqlalchemy.orm import Session

from app.audit.logger import AuditLogger
from app.models.enums import CaseStatus
from app.repositories.audit import AuditEventRepository
from app.repositories.cases import CaseRepository
from app.schemas.cases import CaseCreateRequest, CaseStatusTransitionRequest
from app.services.cases import CaseService


def build_case_service(db_session: Session) -> CaseService:
    return CaseService(CaseRepository(db_session), AuditLogger(AuditEventRepository(db_session)))


def test_create_case_persists_case_and_audit_event(db_session: Session) -> None:
    service = build_case_service(db_session)

    response = service.create_case(
        CaseCreateRequest(
            case_reference="CASE-001",
            case_type="account_opening",
            actor_id="ops-user-1",
        )
    )

    assert response.status == CaseStatus.CREATED
    assert len(AuditEventRepository(db_session).list_for_case(response.id)[0]) == 1


def test_transition_case_persists_status_and_audit_event(db_session: Session) -> None:
    service = build_case_service(db_session)
    created = service.create_case(
        CaseCreateRequest(
            case_reference="CASE-002",
            case_type="loan_review",
            actor_id="ops-user-1",
        )
    )

    transitioned = service.transition_case(
        case_id=created.id,
        request=CaseStatusTransitionRequest(
            to_status=CaseStatus.DOCUMENTS_UPLOADED,
            actor_id="ops-user-1",
        ),
    )

    assert transitioned.from_status == CaseStatus.CREATED
    assert transitioned.to_status == CaseStatus.DOCUMENTS_UPLOADED
    assert len(AuditEventRepository(db_session).list_for_case(created.id)[0]) == 2


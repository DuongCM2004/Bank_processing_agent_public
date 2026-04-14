from __future__ import annotations

from fastapi import APIRouter, Depends

from ops_agent.api.dependencies import get_case_application_service
from ops_agent.application.services.case_application_service import CaseApplicationService
from ops_agent.models import (
    CaseCreateRequest,
    CaseCreateResponse,
    CaseRecord,
    CaseResults,
    CaseStatusView,
    CloseCaseRequest,
    DecisionRecord,
    DocumentCreate,
    DocumentRecord,
    EscalationRequest,
    FieldCorrectionRequest,
    ProcessingAcceptedResponse,
    ProcessingTriggerRequest,
    RevalidateRequest,
)

router = APIRouter(prefix="/v1/cases", tags=["cases"])


@router.post("", response_model=CaseCreateResponse, status_code=201)
def create_case(
    request: CaseCreateRequest,
    service: CaseApplicationService = Depends(get_case_application_service),
) -> CaseCreateResponse:
    return service.create_case(request)


@router.get("/{case_id}", response_model=CaseRecord)
def get_case(case_id: str, service: CaseApplicationService = Depends(get_case_application_service)) -> CaseRecord:
    return service.get_case(case_id)


@router.post("/{case_id}/documents", response_model=DocumentRecord, status_code=201)
def add_document(
    case_id: str,
    request: DocumentCreate,
    service: CaseApplicationService = Depends(get_case_application_service),
) -> DocumentRecord:
    return service.add_document(case_id, request)


@router.get("/{case_id}/documents/{document_id}", response_model=DocumentRecord)
def get_document(
    case_id: str,
    document_id: str,
    service: CaseApplicationService = Depends(get_case_application_service),
) -> DocumentRecord:
    return service.get_document(case_id, document_id)


@router.get("/{case_id}/results", response_model=CaseResults)
def get_results(case_id: str, service: CaseApplicationService = Depends(get_case_application_service)) -> CaseResults:
    return service.get_results(case_id)


@router.post("/{case_id}/process", response_model=ProcessingAcceptedResponse, status_code=202)
def start_processing(
    case_id: str,
    request: ProcessingTriggerRequest,
    service: CaseApplicationService = Depends(get_case_application_service),
) -> ProcessingAcceptedResponse:
    return service.start_processing(case_id, request)


@router.get("/{case_id}/status", response_model=CaseStatusView)
def get_case_status(
    case_id: str,
    service: CaseApplicationService = Depends(get_case_application_service),
) -> CaseStatusView:
    return service.get_case_status(case_id)


@router.get("/{case_id}/decisions/latest", response_model=DecisionRecord)
def get_latest_decision(
    case_id: str,
    service: CaseApplicationService = Depends(get_case_application_service),
) -> DecisionRecord:
    return service.get_latest_decision(case_id)


@router.post("/{case_id}/field-corrections", response_model=CaseRecord)
def submit_field_corrections(
    case_id: str,
    request: FieldCorrectionRequest,
    service: CaseApplicationService = Depends(get_case_application_service),
) -> CaseRecord:
    return service.submit_field_corrections(case_id, request)


@router.post("/{case_id}/escalations", response_model=CaseRecord)
def escalate_case(
    case_id: str,
    request: EscalationRequest,
    service: CaseApplicationService = Depends(get_case_application_service),
) -> CaseRecord:
    return service.escalate_case(case_id, request)


@router.post("/{case_id}/revalidate", response_model=CaseRecord)
def revalidate_case(
    case_id: str,
    request: RevalidateRequest,
    service: CaseApplicationService = Depends(get_case_application_service),
) -> CaseRecord:
    return service.revalidate_case(case_id, request)


@router.post("/{case_id}/close", response_model=CaseRecord)
def close_case(
    case_id: str,
    request: CloseCaseRequest,
    service: CaseApplicationService = Depends(get_case_application_service),
) -> CaseRecord:
    return service.close_case(case_id, request)

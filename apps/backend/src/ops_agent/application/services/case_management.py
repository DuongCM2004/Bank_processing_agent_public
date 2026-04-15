from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from ops_agent.api.schemas import (
    AuditEventResponse,
    CaseCreateRequest,
    CaseCreateResponse,
    CaseDetailResponse,
    CaseListResponse,
    CaseSummaryResponse,
    DecisionResponse,
    DecisionFindingLinkResponse,
    DocumentUploadMetadataResponse,
    ExtractionResultResponse,
    ManualReviewActionResponse,
    OCRResultResponse,
    RoleResponse,
    UpdateCaseStatusRequest,
    UpdateCaseStatusResponse,
    UserSummaryResponse,
    ValidationFindingResponse,
    ValidationResultResponse,
    RiskFindingResponse,
    ComplianceFindingResponse,
    EvidenceReferenceResponse,
)
from ops_agent.application.services.case_workflow import CaseWorkflowService
from ops_agent.application.services.audit import AuditActor, AuditEventCommand, AuditService, AuditTarget
from ops_agent.domain.shared.enums import (
    AuditActorType,
    AuditEventType,
    CaseStatus,
    DocumentStatus,
    FindingSeverity,
    FindingStatus,
    RiskLevel,
)
from ops_agent.domain.shared.exceptions import ResourceNotFoundError
from ops_agent.domain.workflow import CaseTransitionAuditHook, CaseTransitionAuditRecord, CaseTransitionContext
from ops_agent.infrastructure.db.models import Case, Document
from ops_agent.infrastructure.db.repositories import CaseListFilters, CaseRepository


class SQLAlchemyCaseTransitionAuditHook(CaseTransitionAuditHook):
    def __init__(self, audit_service: AuditService) -> None:
        self._audit_service = audit_service

    def record_transition(self, event: CaseTransitionAuditRecord) -> None:
        self._audit_service.record_case_transition(event)


class CaseManagementService:
    def __init__(
        self,
        repository: CaseRepository,
        workflow_service: CaseWorkflowService,
        audit_service: AuditService,
    ) -> None:
        self._repository = repository
        self._workflow_service = workflow_service
        self._audit_service = audit_service

    def create_case(self, request: CaseCreateRequest) -> CaseCreateResponse:
        now = datetime.now(UTC)
        case = Case(
            case_reference=_new_case_reference(),
            case_type=request.case_type,
            status=CaseStatus.CREATED,
            status_changed_at=now,
            current_queue=request.current_queue,
            source_channel=request.source_channel,
            customer_reference=request.customer_reference,
            submitted_by_user_id=request.submitted_by_user_id,
            case_metadata=request.metadata,
            created_by=str(request.submitted_by_user_id) if request.submitted_by_user_id else None,
            updated_by=str(request.submitted_by_user_id) if request.submitted_by_user_id else None,
        )
        self._repository.add(case)
        self._repository.flush()

        for document_request in request.documents:
            document = Document(
                case_id=case.id,
                filename=document_request.filename,
                document_type=document_request.document_type,
                mime_type=document_request.mime_type,
                storage_key=document_request.storage_key,
                sha256_digest=document_request.sha256_digest,
                file_size_bytes=document_request.file_size_bytes,
                uploaded_at=now,
                status=DocumentStatus.UPLOADED,
                status_changed_at=now,
                source_channel=document_request.source_channel,
                page_count=document_request.page_count,
                uploaded_by_user_id=request.submitted_by_user_id,
                document_metadata=document_request.metadata,
                created_by=str(request.submitted_by_user_id) if request.submitted_by_user_id else None,
                updated_by=str(request.submitted_by_user_id) if request.submitted_by_user_id else None,
            )
            case.documents.append(document)
            self._repository.flush()
            self._audit_service.record_event(
                AuditEventCommand(
                    event_type=AuditEventType.DOCUMENT_ADDED,
                    summary=f"Document '{document_request.filename}' was registered on case creation.",
                    target=AuditTarget(resource_type="document", resource_id=document.id, case_id=case.id),
                    actor=AuditActor(
                        actor_type=AuditActorType.USER if request.submitted_by_user_id else AuditActorType.SYSTEM,
                        actor_identifier=str(request.submitted_by_user_id) if request.submitted_by_user_id else "system",
                        actor_user_id=request.submitted_by_user_id,
                    ),
                    metadata_payload={"filename": document_request.filename, "document_type": document_request.document_type},
                    occurred_at=now,
                    created_by=str(request.submitted_by_user_id) if request.submitted_by_user_id else None,
                    updated_by=str(request.submitted_by_user_id) if request.submitted_by_user_id else None,
                )
            )

        self._audit_service.record_event(
            AuditEventCommand(
                event_type=AuditEventType.CASE_CREATED,
                summary=f"Case '{case.case_reference}' was created.",
                target=AuditTarget(resource_type="case", resource_id=case.id, case_id=case.id),
                actor=AuditActor(
                    actor_type=AuditActorType.USER if request.submitted_by_user_id else AuditActorType.SYSTEM,
                    actor_identifier=str(request.submitted_by_user_id) if request.submitted_by_user_id else "system",
                    actor_user_id=request.submitted_by_user_id,
                ),
                metadata_payload={"case_type": case.case_type, "document_count": len(case.documents)},
                occurred_at=now,
                created_by=str(request.submitted_by_user_id) if request.submitted_by_user_id else None,
                updated_by=str(request.submitted_by_user_id) if request.submitted_by_user_id else None,
            )
        )

        if case.documents:
            self._workflow_service.transition(
                case=case,
                to_status=CaseStatus.DOCUMENTS_UPLOADED,
                context=CaseTransitionContext(
                    actor_type=AuditActorType.USER if request.submitted_by_user_id else AuditActorType.SYSTEM,
                    actor_id=str(request.submitted_by_user_id) if request.submitted_by_user_id else "system",
                    reason_code="documents_uploaded",
                    metadata={"document_count": len(case.documents)},
                    occurred_at=now,
                ),
            )

        self._repository.commit()
        self._repository.refresh(case)
        return self._to_case_create_response(case)

    def get_case(self, case_id: UUID) -> CaseSummaryResponse:
        case = self._repository.get_by_id(case_id)
        if case is None:
            raise ResourceNotFoundError("Case", str(case_id))
        return self._to_case_summary(case)

    def get_case_detail(self, case_id: UUID) -> CaseDetailResponse:
        case = self._repository.get_detail_by_id(case_id)
        if case is None:
            raise ResourceNotFoundError("Case", str(case_id))
        return self._to_case_detail(case)

    def list_cases(
        self,
        *,
        limit: int,
        offset: int,
        status: CaseStatus | None = None,
        current_queue: str | None = None,
        case_type: str | None = None,
    ) -> CaseListResponse:
        items, total = self._repository.list_cases(
            filters=CaseListFilters(status=status, current_queue=current_queue, case_type=case_type),
            limit=limit,
            offset=offset,
        )
        return CaseListResponse(
            items=[self._to_case_summary(case) for case in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    def update_case_status(self, *, case_id: UUID, request: UpdateCaseStatusRequest) -> UpdateCaseStatusResponse:
        case = self._repository.get_by_id(case_id)
        if case is None:
            raise ResourceNotFoundError("Case", str(case_id))

        occurred_at = datetime.now(UTC)
        self._workflow_service.transition(
            case=case,
            to_status=request.target_status,
            context=CaseTransitionContext(
                actor_type=request.actor_type,
                actor_id=request.actor_id,
                reason_code=request.reason_code,
                comment=request.comment,
                metadata=request.metadata,
                occurred_at=occurred_at,
            ),
        )
        if request.target_status in {CaseStatus.APPROVED, CaseStatus.REJECTED}:
            case.closed_at = occurred_at

        self._repository.commit()
        self._repository.refresh(case)
        return UpdateCaseStatusResponse(
            id=case.id,
            status=case.status,
            status_changed_at=case.status_changed_at,
            updated_at=case.updated_at,
            allowed_next_statuses=list(self._workflow_service.allowed_targets(case.status)),
        )

    def _to_case_create_response(self, case: Case) -> CaseCreateResponse:
        return CaseCreateResponse(
            id=case.id,
            case_reference=case.case_reference,
            case_type=case.case_type,
            status=case.status,
            status_changed_at=case.status_changed_at,
            current_queue=case.current_queue,
            source_channel=case.source_channel,
            customer_reference=case.customer_reference,
            submitted_by_user_id=case.submitted_by_user_id,
            metadata=case.case_metadata,
            documents=[self._to_document_response(document) for document in case.documents],
            created_at=case.created_at,
            updated_at=case.updated_at,
        )

    def _to_case_summary(self, case: Case) -> CaseSummaryResponse:
        return CaseSummaryResponse(
            id=case.id,
            case_reference=case.case_reference,
            case_type=case.case_type,
            status=case.status,
            status_changed_at=case.status_changed_at,
            current_queue=case.current_queue,
            source_channel=case.source_channel,
            customer_reference=case.customer_reference,
            document_count=len(case.documents),
            created_at=case.created_at,
            updated_at=case.updated_at,
        )

    def _to_case_detail(self, case: Case) -> CaseDetailResponse:
        documents = [self._to_document_response(document) for document in case.documents]
        ocr_results = [self._to_ocr_result_response(result) for document in case.documents for result in document.ocr_results]
        extraction_results = [
            self._to_extraction_result_response(result) for document in case.documents for result in document.extraction_results
        ]
        return CaseDetailResponse(
            id=case.id,
            case_reference=case.case_reference,
            case_type=case.case_type,
            status=case.status,
            status_changed_at=case.status_changed_at,
            current_queue=case.current_queue,
            source_channel=case.source_channel,
            customer_reference=case.customer_reference,
            submitted_by_user=self._to_user_summary(case.submitted_by_user) if case.submitted_by_user else None,
            metadata=case.case_metadata,
            documents=documents,
            ocr_results=ocr_results,
            extraction_results=extraction_results,
            validation=ValidationResultResponse(
                case_id=case.id,
                validation_findings=[self._to_validation_finding_response(item) for item in case.validation_findings],
                risk_findings=[self._to_risk_finding_response(item) for item in case.risk_findings],
                compliance_findings=[self._to_compliance_finding_response(item) for item in case.compliance_findings],
                has_blocking_findings=_has_blocking_findings(case),
            ),
            decisions=[self._to_decision_response(item) for item in case.decisions],
            manual_review_actions=[self._to_manual_review_action_response(item) for item in case.manual_review_actions],
            audit_events=[self._to_audit_event_response(item) for item in case.audit_events],
            created_at=case.created_at,
            updated_at=case.updated_at,
            closed_at=case.closed_at,
        )

    def _to_document_response(self, document: Document) -> DocumentUploadMetadataResponse:
        return DocumentUploadMetadataResponse(
            id=document.id,
            case_id=document.case_id,
            filename=document.filename,
            document_type=document.document_type,
            mime_type=document.mime_type,
            source_channel=document.source_channel,
            storage_key=document.storage_key,
            sha256_digest=document.sha256_digest,
            file_size_bytes=document.file_size_bytes,
            uploaded_at=document.uploaded_at,
            status=document.status,
            status_changed_at=document.status_changed_at,
            page_count=document.page_count,
            metadata=document.document_metadata,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    def _to_ocr_result_response(self, result) -> OCRResultResponse:
        return OCRResultResponse(
            id=result.id,
            document_id=result.document_id,
            status=result.status,
            raw_text=result.raw_text,
            confidence_score=result.confidence_score,
            provider_name=result.provider_name,
            provider_job_id=result.provider_job_id,
            processed_at=result.processed_at,
            page_count=result.page_count,
            result_metadata=result.result_metadata,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

    def _to_extraction_result_response(self, result) -> ExtractionResultResponse:
        return ExtractionResultResponse(
            id=result.id,
            document_id=result.document_id,
            ocr_result_id=result.ocr_result_id,
            status=result.status,
            schema_name=result.schema_name,
            extracted_payload=result.extracted_payload,
            confidence_score=result.confidence_score,
            evidence_refs=[EvidenceReferenceResponse.model_validate(item) for item in result.evidence_refs],
            provider_name=result.provider_name,
            provider_job_id=result.provider_job_id,
            processed_at=result.processed_at,
            model_version=result.model_version,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

    def _to_validation_finding_response(self, item) -> ValidationFindingResponse:
        return ValidationFindingResponse(
            id=item.id,
            case_id=item.case_id,
            document_id=item.document_id,
            extraction_result_id=item.extraction_result_id,
            rule_code=item.rule_code,
            field_name=item.field_name,
            message=item.message,
            severity=item.severity,
            status=item.status,
            resolution_note=item.resolution_note,
            evidence_refs=[EvidenceReferenceResponse.model_validate(ref) for ref in item.evidence_refs],
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _to_risk_finding_response(self, item) -> RiskFindingResponse:
        return RiskFindingResponse(
            id=item.id,
            case_id=item.case_id,
            document_id=item.document_id,
            extraction_result_id=item.extraction_result_id,
            risk_code=item.risk_code,
            message=item.message,
            risk_level=item.risk_level,
            status=item.status,
            risk_score=item.risk_score,
            evidence_refs=[EvidenceReferenceResponse.model_validate(ref) for ref in item.evidence_refs],
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _to_compliance_finding_response(self, item) -> ComplianceFindingResponse:
        return ComplianceFindingResponse(
            id=item.id,
            case_id=item.case_id,
            document_id=item.document_id,
            extraction_result_id=item.extraction_result_id,
            policy_code=item.policy_code,
            regulation_reference=item.regulation_reference,
            message=item.message,
            severity=item.severity,
            status=item.status,
            evidence_refs=[EvidenceReferenceResponse.model_validate(ref) for ref in item.evidence_refs],
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _to_decision_response(self, item) -> DecisionResponse:
        return DecisionResponse(
            id=item.id,
            case_id=item.case_id,
            decided_by_user_id=item.decided_by_user_id,
            decision_type=item.decision_type,
            outcome=item.outcome,
            reason_code=item.reason_code,
            rationale=item.rationale,
            confidence_score=item.confidence_score,
            evidence_refs=[EvidenceReferenceResponse.model_validate(ref) for ref in item.evidence_refs],
            linked_findings=[DecisionFindingLinkResponse.model_validate(link) for link in item.linked_findings],
            supersedes_decision_id=item.supersedes_decision_id,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _to_manual_review_action_response(self, item) -> ManualReviewActionResponse:
        return ManualReviewActionResponse(
            id=item.id,
            case_id=item.case_id,
            document_id=item.document_id,
            performed_by_user_id=item.performed_by_user_id,
            related_decision_id=item.related_decision_id,
            action_type=item.action_type,
            comment=item.comment,
            payload=item.payload,
            evidence_refs=[EvidenceReferenceResponse.model_validate(ref) for ref in item.evidence_refs],
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _to_audit_event_response(self, item) -> AuditEventResponse:
        return AuditService.to_response(item)

    def _to_user_summary(self, user) -> UserSummaryResponse:
        return UserSummaryResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            status=user.status,
            roles=[RoleResponse(id=role.id, code=role.code, name=role.name, description=role.description) for role in user.roles],
        )


def _new_case_reference() -> str:
    return f"CASE-{uuid4().hex[:10].upper()}"


def _maybe_uuid(value: str | None) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(value)
    except ValueError:
        return None


def _has_blocking_findings(case: Case) -> bool:
    validation_blocking = any(
        finding.status == FindingStatus.OPEN and finding.severity in {FindingSeverity.ERROR, FindingSeverity.CRITICAL}
        for finding in case.validation_findings
    )
    compliance_blocking = any(
        finding.status == FindingStatus.OPEN and finding.severity in {FindingSeverity.ERROR, FindingSeverity.CRITICAL}
        for finding in case.compliance_findings
    )
    risk_blocking = any(
        finding.status == FindingStatus.OPEN and finding.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}
        for finding in case.risk_findings
    )
    return validation_blocking or compliance_blocking or risk_blocking

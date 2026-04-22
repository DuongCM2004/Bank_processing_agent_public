from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable
from uuid import UUID, uuid4

from ops_agent.application.services.case_workflow import CaseWorkflowService
from ops_agent.config import ProcessingSettings, WorkerSettings
from ops_agent.domain.shared.evidence import EvidenceRef
from ops_agent.domain.shared.enums import (
    AuditActorType,
    AuditEventType,
    CaseStatus,
    DecisionOutcome,
    DecisionType,
    DocumentStatus,
    FindingStatus,
    ProcessingStatus,
)
from ops_agent.domain.shared.exceptions import CaseProcessingExecutionError, ConflictError, ResourceNotFoundError
from ops_agent.domain.workflow import CaseTransitionAuditHook, CaseTransitionAuditRecord, CaseTransitionContext
from ops_agent.infrastructure.db.models import (
    AuditEvent,
    Case,
    ComplianceFinding,
    Decision,
    Document,
    ExtractionResult,
    OCRResult,
    RiskFinding,
    ValidationFinding,
)
from ops_agent.infrastructure.db.repositories.processing_repository import ProcessingRepository
from ops_agent.infrastructure.providers.interfaces import (
    DocumentClassificationProvider,
    DocumentClassificationProviderRequest,
    ExtractionProvider,
    ExtractionProviderRequest,
    OCRProvider,
    OCRProviderRequest,
    ValidationDocumentContext,
    ValidationRulesEngine,
    ValidationRulesEngineRequest,
)
from ops_agent.infrastructure.queue.contracts import CaseProcessingTask, TaskDispatcher
from ops_agent.infrastructure.storage.protocols import DocumentStorage


SERVICE_ACTOR_ID = "ops-agent-case-orchestrator"


class SQLAlchemyCaseProcessingTransitionAuditHook(CaseTransitionAuditHook):
    def __init__(self, repository: ProcessingRepository) -> None:
        self._repository = repository

    def record_transition(self, event: CaseTransitionAuditRecord) -> None:
        self._repository.add_audit_event(
            AuditEvent(
                case_id=event.case_id,
                actor_user_id=_maybe_uuid(event.actor_id) if event.actor_type == AuditActorType.USER else None,
                actor_type=event.actor_type,
                actor_identifier=event.actor_id,
                event_type=event.event_type,
                resource_type="case",
                resource_id=event.case_id,
                occurred_at=event.occurred_at,
                details={
                    "from_status": event.from_status.value,
                    "to_status": event.to_status.value,
                    "transition_name": event.transition_name,
                    "reason_code": event.reason_code,
                    "comment": event.comment,
                    "metadata": event.metadata,
                },
                evidence_refs=[],
                created_by=event.actor_id,
                updated_by=event.actor_id,
            )
        )


@dataclass(frozen=True, slots=True)
class CaseProcessingRetryPolicy:
    max_attempts: int = 3


@dataclass(frozen=True, slots=True)
class PersistedDocumentArtifacts:
    document: Document
    ocr_result: OCRResult
    extraction_result: ExtractionResult
    effective_document_type: str


@dataclass(frozen=True, slots=True)
class ValidationPlan:
    validation_findings: tuple[dict[str, object], ...] = ()
    risk_findings: tuple[dict[str, object], ...] = ()
    compliance_findings: tuple[dict[str, object], ...] = ()
    requires_manual_review: bool = False
    rationale: str = ""
    recommendation_reason_code: str = "system_recommendation_ready"
    recommendation_outcome: DecisionOutcome = DecisionOutcome.APPROVED


@dataclass(frozen=True, slots=True)
class CaseProcessingResult:
    case_id: UUID
    correlation_id: str
    attempt_number: int
    final_status: CaseStatus
    processed_document_count: int
    validation_finding_count: int
    risk_finding_count: int
    compliance_finding_count: int
    manual_review_required: bool
    decision_id: UUID | None = None


class CaseProcessingService:
    def __init__(
        self,
        *,
        repository: ProcessingRepository,
        workflow_service: CaseWorkflowService,
        storage: DocumentStorage,
        ocr_provider: OCRProvider,
        classification_provider: DocumentClassificationProvider,
        extraction_provider: ExtractionProvider,
        validation_engine: ValidationRulesEngine,
        processing_settings: ProcessingSettings,
        worker_settings: WorkerSettings,
        task_dispatcher: TaskDispatcher | None = None,
        service_actor_id: str = SERVICE_ACTOR_ID,
    ) -> None:
        self._repository = repository
        self._workflow_service = workflow_service
        self._storage = storage
        self._ocr_provider = ocr_provider
        self._classification_provider = classification_provider
        self._extraction_provider = extraction_provider
        self._validation_engine = validation_engine
        self._processing_settings = processing_settings
        self._worker_settings = worker_settings
        self._task_dispatcher = task_dispatcher
        self._service_actor_id = service_actor_id
        self._retry_policy = CaseProcessingRetryPolicy(max_attempts=processing_settings.max_retry_attempts)

    def queue_case_for_processing(
        self,
        *,
        case_id: UUID,
        requested_by: str | None = None,
        attempt_number: int = 1,
        correlation_id: str | None = None,
    ) -> CaseProcessingTask:
        if attempt_number > self._retry_policy.max_attempts:
            raise ConflictError(
                f"Retry limit exceeded for case '{case_id}'. Maximum attempts: {self._retry_policy.max_attempts}.",
                error_code="processing_retry_limit_exceeded",
            )

        case = self._get_case(case_id)
        if not case.documents:
            raise ConflictError(
                f"Case '{case_id}' cannot be queued because it has no uploaded documents.",
                error_code="case_has_no_documents",
            )

        task = CaseProcessingTask(
            case_id=case.id,
            correlation_id=correlation_id or str(uuid4()),
            attempt_number=attempt_number,
            requested_by=requested_by,
        )
        actor_id = requested_by or self._service_actor_id
        occurred_at = datetime.now(UTC)
        self._workflow_service.transition(
            case=case,
            to_status=CaseStatus.QUEUED_FOR_PROCESSING,
            context=CaseTransitionContext(
                actor_type=AuditActorType.SERVICE,
                actor_id=actor_id,
                reason_code="queued_for_processing",
                metadata={
                    "correlation_id": task.correlation_id,
                    "attempt_number": task.attempt_number,
                    "queue_name": self._worker_settings.task_queue_name,
                },
                occurred_at=occurred_at,
            ),
        )
        self._repository.commit()

        if self._task_dispatcher is not None:
            try:
                self._task_dispatcher.enqueue(task.to_envelope(), queue_name=self._worker_settings.task_queue_name)
            except Exception as exc:
                self._repository.rollback()
                failed_case = self._get_case(case_id)
                self._transition_case_to_failed(
                    case=failed_case,
                    actor_id=actor_id,
                    reason_comment=f"Queue dispatch failed: {exc}",
                    metadata={"correlation_id": task.correlation_id, "attempt_number": task.attempt_number},
                    occurred_at=datetime.now(UTC),
                )
                self._repository.commit()
                raise CaseProcessingExecutionError(str(case_id)) from exc

        return task

    def process_case(self, task: CaseProcessingTask) -> CaseProcessingResult:
        case = self._get_case(task.case_id)
        if case.status != CaseStatus.QUEUED_FOR_PROCESSING:
            raise ConflictError(
                f"Case '{case.id}' must be queued before processing. Current status: '{case.status.value}'.",
                error_code="case_not_queued_for_processing",
            )
        if not case.documents:
            raise ConflictError(
                f"Case '{case.id}' cannot be processed because it has no uploaded documents.",
                error_code="case_has_no_documents",
            )

        started_at = datetime.now(UTC)
        self._workflow_service.transition(
            case=case,
            to_status=CaseStatus.PROCESSING,
            context=CaseTransitionContext(
                actor_type=AuditActorType.SERVICE,
                actor_id=self._service_actor_id,
                reason_code="processing_started",
                metadata={"correlation_id": task.correlation_id, "attempt_number": task.attempt_number},
                occurred_at=started_at,
            ),
        )
        for document in case.documents:
            self._set_document_status(document, DocumentStatus.OCR_PENDING, occurred_at=started_at)
        self._repository.commit()

        try:
            persisted_artifacts = [self._process_document(case=case, document=document) for document in case.documents]

            extraction_completed_at = datetime.now(UTC)
            self._workflow_service.transition(
                case=case,
                to_status=CaseStatus.EXTRACTION_COMPLETED,
                context=CaseTransitionContext(
                    actor_type=AuditActorType.SERVICE,
                    actor_id=self._service_actor_id,
                    reason_code="extraction_completed",
                    metadata={
                        "correlation_id": task.correlation_id,
                        "document_count": len(persisted_artifacts),
                    },
                    occurred_at=extraction_completed_at,
                ),
            )

            validation_plan = self._build_validation_plan(persisted_artifacts)
            self._persist_validation_plan(case=case, validation_plan=validation_plan)

            validation_completed_at = datetime.now(UTC)
            self._workflow_service.transition(
                case=case,
                to_status=CaseStatus.VALIDATION_COMPLETED,
                context=CaseTransitionContext(
                    actor_type=AuditActorType.SERVICE,
                    actor_id=self._service_actor_id,
                    reason_code="validation_completed",
                    metadata={
                        "correlation_id": task.correlation_id,
                        "validation_findings": len(validation_plan.validation_findings),
                        "risk_findings": len(validation_plan.risk_findings),
                        "compliance_findings": len(validation_plan.compliance_findings),
                    },
                    occurred_at=validation_completed_at,
                ),
            )

            decision = self._record_system_decision(case=case, validation_plan=validation_plan)
            final_status = CaseStatus.MANUAL_REVIEW_REQUIRED if validation_plan.requires_manual_review else CaseStatus.DECISION_READY
            final_reason = "manual_review_required" if validation_plan.requires_manual_review else "decision_ready"
            final_transition_at = datetime.now(UTC)
            self._workflow_service.transition(
                case=case,
                to_status=final_status,
                context=CaseTransitionContext(
                    actor_type=AuditActorType.SERVICE,
                    actor_id=self._service_actor_id,
                    reason_code=final_reason,
                    metadata={
                        "correlation_id": task.correlation_id,
                        "decision_id": str(decision.id),
                        "manual_review_required": validation_plan.requires_manual_review,
                    },
                    occurred_at=final_transition_at,
                ),
            )

            if validation_plan.requires_manual_review:
                for artifact in persisted_artifacts:
                    self._set_document_status(artifact.document, DocumentStatus.REVIEW_REQUIRED, occurred_at=final_transition_at)

            self._repository.commit()
            self._repository.refresh(case)

            return CaseProcessingResult(
                case_id=case.id,
                correlation_id=task.correlation_id,
                attempt_number=task.attempt_number,
                final_status=case.status,
                processed_document_count=len(persisted_artifacts),
                validation_finding_count=len(validation_plan.validation_findings),
                risk_finding_count=len(validation_plan.risk_findings),
                compliance_finding_count=len(validation_plan.compliance_findings),
                manual_review_required=validation_plan.requires_manual_review,
                decision_id=decision.id,
            )
        except Exception as exc:
            self._repository.rollback()
            failed_case = self._get_case(task.case_id)
            failure_time = datetime.now(UTC)
            for document in failed_case.documents:
                self._set_document_status(document, DocumentStatus.FAILED, occurred_at=failure_time)
            self._transition_case_to_failed(
                case=failed_case,
                actor_id=self._service_actor_id,
                reason_comment=str(exc),
                metadata={"correlation_id": task.correlation_id, "attempt_number": task.attempt_number},
                occurred_at=failure_time,
            )
            self._repository.commit()
            raise CaseProcessingExecutionError(str(task.case_id)) from exc

    def _get_case(self, case_id: UUID) -> Case:
        case = self._repository.get_case_for_processing(case_id)
        if case is None:
            raise ResourceNotFoundError("Case", str(case_id))
        return case

    def _process_document(self, *, case: Case, document: Document) -> PersistedDocumentArtifacts:
        stored_document = self._storage.resolve(storage_key=document.storage_key)
        content = Path(stored_document.absolute_path).read_bytes()

        ocr_response = self._ocr_provider.process(
            OCRProviderRequest(
                case_id=case.id,
                document_id=document.id,
                filename=document.filename,
                mime_type=document.mime_type,
                content=content,
            )
        )
        now = datetime.now(UTC)
        ocr_result = OCRResult(
            document_id=document.id,
            status=ProcessingStatus.COMPLETED,
            raw_text=ocr_response.raw_text,
            confidence_score=ocr_response.confidence_score,
            provider_name=ocr_response.provider_name,
            provider_job_id=ocr_response.provider_job_id,
            processed_at=now,
            page_count=ocr_response.page_count,
            result_metadata=ocr_response.result_metadata,
            created_by=self._service_actor_id,
            updated_by=self._service_actor_id,
        )
        self._repository.add_ocr_result(ocr_result)
        self._repository.flush()
        self._set_document_status(document, DocumentStatus.OCR_COMPLETED, occurred_at=now)
        self._repository.add_audit_event(
            self._build_audit_event(
                case_id=case.id,
                resource_type="ocr_result",
                resource_id=ocr_result.id,
                event_type=AuditEventType.OCR_COMPLETED,
                occurred_at=now,
                details={"document_id": str(document.id), "provider_name": ocr_result.provider_name},
            )
        )

        classification_response = self._classification_provider.process(
            DocumentClassificationProviderRequest(
                case_id=case.id,
                document_id=document.id,
                filename=document.filename,
                mime_type=document.mime_type,
                current_document_type=document.document_type,
                raw_text=ocr_result.raw_text or "",
                metadata=document.document_metadata,
            )
        )
        effective_document_type = self._resolve_document_type(
            current_document_type=document.document_type,
            classified_document_type=classification_response.document_type,
        )
        document.document_type = effective_document_type
        document.document_metadata = {
            **document.document_metadata,
            "classified_document_type": classification_response.document_type,
            "classification_confidence_score": str(classification_response.confidence_score or 0.0),
            "classification_provider": classification_response.provider_name,
        }

        extraction_response = self._extraction_provider.process(
            ExtractionProviderRequest(
                case_id=case.id,
                document_id=document.id,
                document_type=effective_document_type,
                filename=document.filename,
                raw_text=ocr_result.raw_text or "",
                mime_type=document.mime_type,
                content=content,
            )
        )
        effective_document_type = self._resolve_extracted_document_type(
            current_document_type=effective_document_type,
            extracted_payload=extraction_response.extracted_payload,
        )
        document.document_type = effective_document_type
        extraction_at = datetime.now(UTC)
        extraction_result = ExtractionResult(
            document_id=document.id,
            ocr_result_id=ocr_result.id,
            status=ProcessingStatus.COMPLETED,
            schema_name=extraction_response.schema_name,
            extracted_payload=extraction_response.extracted_payload,
            confidence_score=extraction_response.confidence_score,
            evidence_refs=[evidence_ref.to_record() for evidence_ref in extraction_response.evidence_refs],
            provider_name=extraction_response.provider_name,
            provider_job_id=extraction_response.provider_job_id,
            processed_at=extraction_at,
            model_version=extraction_response.model_version,
            created_by=self._service_actor_id,
            updated_by=self._service_actor_id,
        )
        self._repository.add_extraction_result(extraction_result)
        self._repository.flush()
        self._set_document_status(document, DocumentStatus.EXTRACTION_COMPLETED, occurred_at=extraction_at)
        self._repository.add_audit_event(
            self._build_audit_event(
                case_id=case.id,
                resource_type="extraction_result",
                resource_id=extraction_result.id,
                event_type=AuditEventType.EXTRACTION_COMPLETED,
                occurred_at=extraction_at,
                details={
                    "document_id": str(document.id),
                    "provider_name": extraction_result.provider_name,
                    "schema_name": extraction_result.schema_name,
                },
            )
        )
        return PersistedDocumentArtifacts(
            document=document,
            ocr_result=ocr_result,
            extraction_result=extraction_result,
            effective_document_type=effective_document_type,
        )

    def _build_validation_plan(self, persisted_artifacts: Iterable[PersistedDocumentArtifacts]) -> ValidationPlan:
        artifacts = tuple(persisted_artifacts)
        engine_result = self._validation_engine.evaluate(
            ValidationRulesEngineRequest(
                case_id=artifacts[0].document.case_id if artifacts else uuid4(),
                documents=tuple(
                    ValidationDocumentContext(
                        document_id=artifact.document.id,
                        extraction_result_id=artifact.extraction_result.id,
                        document_type=artifact.effective_document_type,
                        filename=artifact.document.filename,
                        raw_text=self._raw_text_for_validation(artifact),
                        ocr_confidence_score=self._ocr_confidence_for_validation(artifact),
                        extracted_payload=artifact.extraction_result.extracted_payload,
                        extraction_confidence_score=artifact.extraction_result.confidence_score,
                        evidence_refs=tuple(_evidence_refs_from_records(artifact.extraction_result.evidence_refs)),
                    )
                    for artifact in artifacts
                ),
                minimum_ocr_confidence=self._processing_settings.min_ocr_confidence,
                minimum_extraction_confidence=self._processing_settings.min_extraction_confidence,
            )
        )

        return ValidationPlan(
            validation_findings=tuple(
                {
                    "document_id": finding.document_id,
                    "extraction_result_id": finding.extraction_result_id,
                    "rule_code": finding.rule_code,
                    "field_name": finding.field_name,
                    "message": finding.message,
                    "severity": finding.severity,
                    "evidence_refs": [evidence_ref.to_record() for evidence_ref in finding.evidence_refs],
                }
                for finding in engine_result.validation_findings
            ),
            risk_findings=tuple(
                {
                    "document_id": finding.document_id,
                    "extraction_result_id": finding.extraction_result_id,
                    "risk_code": finding.risk_code,
                    "message": finding.message,
                    "risk_level": finding.risk_level,
                    "evidence_refs": [evidence_ref.to_record() for evidence_ref in finding.evidence_refs],
                }
                for finding in engine_result.risk_findings
            ),
            compliance_findings=tuple(
                {
                    "document_id": finding.document_id,
                    "extraction_result_id": finding.extraction_result_id,
                    "policy_code": finding.policy_code,
                    "message": finding.message,
                    "severity": finding.severity,
                    "evidence_refs": [evidence_ref.to_record() for evidence_ref in finding.evidence_refs],
                }
                for finding in engine_result.compliance_findings
            ),
            requires_manual_review=engine_result.requires_manual_review,
            rationale=engine_result.rationale,
            recommendation_reason_code=engine_result.recommendation_reason_code,
            recommendation_outcome=engine_result.recommendation_outcome,
        )

    def _persist_validation_plan(self, *, case: Case, validation_plan: ValidationPlan) -> None:
        if validation_plan.validation_findings:
            for finding in validation_plan.validation_findings:
                self._repository.add_validation_finding(
                    ValidationFinding(
                        case_id=case.id,
                        document_id=finding["document_id"],
                        extraction_result_id=finding["extraction_result_id"],
                        rule_code=str(finding["rule_code"]),
                        field_name=finding["field_name"],
                        message=str(finding["message"]),
                        severity=finding["severity"],
                        status=FindingStatus.OPEN,
                        evidence_refs=list(finding["evidence_refs"]),
                        created_by=self._service_actor_id,
                        updated_by=self._service_actor_id,
                    )
                )
        if validation_plan.risk_findings:
            for finding in validation_plan.risk_findings:
                self._repository.add_risk_finding(
                    RiskFinding(
                        case_id=case.id,
                        document_id=finding["document_id"],
                        extraction_result_id=finding["extraction_result_id"],
                        risk_code=str(finding["risk_code"]),
                        message=str(finding["message"]),
                        risk_level=finding["risk_level"],
                        status=FindingStatus.OPEN,
                        evidence_refs=list(finding["evidence_refs"]),
                        created_by=self._service_actor_id,
                        updated_by=self._service_actor_id,
                    )
                )
        if validation_plan.compliance_findings:
            for finding in validation_plan.compliance_findings:
                self._repository.add_compliance_finding(
                    ComplianceFinding(
                        case_id=case.id,
                        document_id=finding["document_id"],
                        extraction_result_id=finding["extraction_result_id"],
                        policy_code=str(finding["policy_code"]),
                        message=str(finding["message"]),
                        severity=finding["severity"],
                        status=FindingStatus.OPEN,
                        evidence_refs=list(finding["evidence_refs"]),
                        created_by=self._service_actor_id,
                        updated_by=self._service_actor_id,
                    )
                )
        if validation_plan.validation_findings or validation_plan.risk_findings or validation_plan.compliance_findings:
            self._repository.add_audit_event(
                self._build_audit_event(
                    case_id=case.id,
                    resource_type="case",
                    resource_id=case.id,
                    event_type=AuditEventType.FINDING_CREATED,
                    occurred_at=datetime.now(UTC),
                    details={
                        "validation_findings": len(validation_plan.validation_findings),
                        "risk_findings": len(validation_plan.risk_findings),
                        "compliance_findings": len(validation_plan.compliance_findings),
                        "requires_manual_review": validation_plan.requires_manual_review,
                    },
                )
            )

    def _record_system_decision(self, *, case: Case, validation_plan: ValidationPlan) -> Decision:
        decision = Decision(
            case_id=case.id,
            decision_type=DecisionType.SYSTEM_RECOMMENDATION,
            outcome=validation_plan.recommendation_outcome,
            reason_code=validation_plan.recommendation_reason_code,
            rationale=validation_plan.rationale,
            confidence_score=0.85 if not validation_plan.requires_manual_review else 0.5,
            evidence_refs=[],
            created_by=self._service_actor_id,
            updated_by=self._service_actor_id,
        )
        self._repository.add_decision(decision)
        self._repository.flush()
        self._repository.add_audit_event(
            self._build_audit_event(
                case_id=case.id,
                resource_type="decision",
                resource_id=decision.id,
                event_type=AuditEventType.DECISION_RECORDED,
                occurred_at=datetime.now(UTC),
                details={
                    "decision_type": decision.decision_type.value,
                    "outcome": decision.outcome.value,
                    "reason_code": decision.reason_code,
                },
            )
        )
        return decision

    def _transition_case_to_failed(
        self,
        *,
        case: Case,
        actor_id: str,
        reason_comment: str,
        metadata: dict[str, object],
        occurred_at: datetime,
    ) -> None:
        if case.status == CaseStatus.FAILED:
            return
        self._workflow_service.transition(
            case=case,
            to_status=CaseStatus.FAILED,
            context=CaseTransitionContext(
                actor_type=AuditActorType.SERVICE,
                actor_id=actor_id,
                reason_code="processing_failed",
                comment=reason_comment[:4000],
                metadata=metadata,
                occurred_at=occurred_at,
            ),
        )

    def _set_document_status(self, document: Document, status: DocumentStatus, *, occurred_at: datetime) -> None:
        document.status = status
        document.status_changed_at = occurred_at
        document.updated_at = occurred_at
        document.updated_by = self._service_actor_id

    def _build_audit_event(
        self,
        *,
        case_id: UUID,
        resource_type: str,
        resource_id: UUID,
        event_type: AuditEventType,
        occurred_at: datetime,
        details: dict[str, object],
    ) -> AuditEvent:
        return AuditEvent(
            case_id=case_id,
            actor_type=AuditActorType.SERVICE,
            actor_identifier=self._service_actor_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            occurred_at=occurred_at,
            details=details,
            evidence_refs=[],
            created_by=self._service_actor_id,
            updated_by=self._service_actor_id,
        )

    @staticmethod
    def _resolve_document_type(*, current_document_type: str, classified_document_type: str) -> str:
        normalized_current = current_document_type.strip().lower()
        if normalized_current and normalized_current not in {"unknown", "unclassified", "generic_document"}:
            return current_document_type
        return classified_document_type

    @staticmethod
    def _resolve_extracted_document_type(
        *,
        current_document_type: str,
        extracted_payload: dict[str, object],
    ) -> str:
        extracted_document_type = extracted_payload.get("document_type")
        if not isinstance(extracted_document_type, str) or not extracted_document_type.strip():
            return current_document_type
        return CaseProcessingService._resolve_document_type(
            current_document_type=current_document_type,
            classified_document_type=extracted_document_type.strip(),
        )

    @staticmethod
    def _raw_text_for_validation(artifact: PersistedDocumentArtifacts) -> str:
        raw_text = artifact.ocr_result.raw_text or ""
        if raw_text.strip():
            return raw_text
        extracted_raw_text = artifact.extraction_result.extracted_payload.get("raw_full_text")
        if isinstance(extracted_raw_text, str):
            return extracted_raw_text
        return ""

    @staticmethod
    def _ocr_confidence_for_validation(artifact: PersistedDocumentArtifacts) -> float | None:
        if artifact.ocr_result.provider_name == "openai_vision_ocr_passthrough":
            return 1.0
        return artifact.ocr_result.confidence_score


def _maybe_uuid(raw: str | None) -> UUID | None:
    if raw is None:
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None


def _evidence_refs_from_records(records: list[dict[str, object]]) -> list:
    return [
        EvidenceRef(
            document_id=UUID(str(record["document_id"])),
            page_number=record.get("page_number"),
            text_anchor=record.get("text_anchor"),
            bounding_box=record.get("bounding_box"),
            extracted_value=record.get("extracted_value"),
            metadata={str(key): str(value) for key, value in dict(record.get("metadata") or {}).items()},
        )
        for record in records
    ]

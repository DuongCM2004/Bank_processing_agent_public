from __future__ import annotations

from datetime import datetime

from ops_agent.models import (
    CaseResults,
    DecisionRecord,
    EvidenceRef,
    ExtractionRunRecord,
    FieldResult,
    ProcessingStatus,
    ValidationResult,
    ValidationRunRecord,
    new_id,
)
from ops_agent.repository import InMemoryRepository


class ResultPersistenceService:
    def __init__(self, repository: InMemoryRepository) -> None:
        self.repository = repository

    def initialize_case_results(self, *, case_id: str, review_required: bool) -> CaseResults:
        results = CaseResults(
            case_id=case_id,
            extraction_status=ProcessingStatus.NOT_STARTED,
            validation_status=ProcessingStatus.NOT_STARTED,
            fields=[
                FieldResult(
                    field_name="review_status",
                    value="pending_processing",
                    normalized_value="pending_processing",
                    confidence=1.0,
                    required=True,
                )
            ],
            validations=[
                ValidationResult(
                    rule_id="routing.default_review",
                    rule_version="0.1.0",
                    result="review_required",
                    severity="warning",
                    reason_code="mvp_default_review_gate" if review_required else "processing_ready",
                )
            ],
            recommended_route="review_required" if review_required else "queued_for_processing",
        )
        self.repository.save_results(results)
        return results

    def mark_processing_started(self, *, case_id: str) -> CaseResults:
        results = self.repository.get_results(case_id)
        if not results:
            raise KeyError(f"Results for case {case_id} were not initialized.")
        results.extraction_status = ProcessingStatus.IN_PROGRESS
        results.validation_status = ProcessingStatus.NOT_STARTED
        self.repository.save_results(results)
        return results

    def record_extraction_results(
        self,
        *,
        case_id: str,
        workflow_run_id: str,
        document_id: str,
        schema_name: str,
        fields: list[FieldResult],
        confidence: float | None,
        recommended_route: str,
        created_at: datetime,
    ) -> ExtractionRunRecord:
        results = self.repository.get_results(case_id)
        if not results:
            raise KeyError(f"Results for case {case_id} were not initialized.")
        results.fields = fields
        results.extraction_status = ProcessingStatus.COMPLETE
        results.recommended_route = recommended_route
        self.repository.save_results(results)
        extraction_run = ExtractionRunRecord(
            extraction_run_id=new_id("extract_run"),
            case_id=case_id,
            workflow_run_id=workflow_run_id,
            document_id=document_id,
            schema_name=schema_name,
            status=ProcessingStatus.COMPLETE,
            field_count=len(fields),
            confidence=confidence,
            recommended_route=recommended_route,
            created_at=created_at,
        )
        self.repository.save_extraction_run(extraction_run)
        return extraction_run

    def record_validation_results(
        self,
        *,
        case_id: str,
        workflow_run_id: str,
        validations: list[ValidationResult],
        recommended_route: str,
        created_at: datetime,
    ) -> ValidationRunRecord:
        results = self.repository.get_results(case_id)
        if not results:
            raise KeyError(f"Results for case {case_id} were not initialized.")
        results.validations = validations
        results.validation_status = ProcessingStatus.COMPLETE
        results.recommended_route = recommended_route
        self.repository.save_results(results)
        validation_run = ValidationRunRecord(
            validation_run_id=new_id("validation_run"),
            case_id=case_id,
            workflow_run_id=workflow_run_id,
            status=ProcessingStatus.COMPLETE,
            finding_count=len(validations),
            recommended_route=recommended_route,
            created_at=created_at,
        )
        self.repository.save_validation_run(validation_run)
        return validation_run

    def record_decision(
        self,
        *,
        case_id: str,
        workflow_run_id: str | None,
        decision_type: str,
        outcome: str,
        actor_id: str,
        actor_type: str,
        reason_code: str,
        created_at: datetime,
        confidence: float | None = None,
        evidence_refs: list[EvidenceRef] | None = None,
    ) -> DecisionRecord:
        decision = DecisionRecord(
            decision_id=new_id("decision"),
            case_id=case_id,
            workflow_run_id=workflow_run_id,
            decision_type=decision_type,
            outcome=outcome,
            actor_id=actor_id,
            actor_type=actor_type,
            reason_code=reason_code,
            confidence=confidence,
            evidence_refs=evidence_refs or [],
            created_at=created_at,
        )
        self.repository.save_decision(decision)
        return decision

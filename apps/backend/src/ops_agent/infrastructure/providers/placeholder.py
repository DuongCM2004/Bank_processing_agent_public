from __future__ import annotations

import re

from ops_agent.domain.shared.enums import DecisionOutcome, FindingSeverity, RiskLevel
from ops_agent.domain.shared.evidence import EvidenceRef
from ops_agent.infrastructure.providers.interfaces import (
    ComplianceFindingResult,
    DocumentClassificationProvider,
    DocumentClassificationProviderRequest,
    DocumentClassificationProviderResult,
    ExtractionProvider,
    ExtractionProviderRequest,
    ExtractionProviderResult,
    OCRProvider,
    OCRProviderRequest,
    OCRProviderResult,
    RiskFindingResult,
    ValidationDocumentContext,
    ValidationFindingResult,
    ValidationRulesEngine,
    ValidationRulesEngineRequest,
    ValidationRulesEngineResult,
)


class PlaceholderOCRProvider(OCRProvider):
    def process(self, request: OCRProviderRequest) -> OCRProviderResult:
        decoded_text = request.content.decode("utf-8", errors="ignore").strip()
        raw_text = decoded_text or f"Simulated OCR text for {request.filename}"
        confidence_score = 0.94 if decoded_text else 0.7
        page_count = max(1, raw_text.count("\f") + 1)
        evidence_refs = (
            EvidenceRef(
                document_id=request.document_id,
                page_number=1,
                text_anchor=raw_text[:120],
                metadata={"source": "placeholder_ocr"},
            ),
        )
        return OCRProviderResult(
            raw_text=raw_text,
            confidence_score=confidence_score,
            provider_name="placeholder_ocr",
            page_count=page_count,
            evidence_refs=evidence_refs,
            result_metadata={"mode": "placeholder", "document_name": request.filename},
        )


class PlaceholderDocumentClassificationProvider(DocumentClassificationProvider):
    def process(self, request: DocumentClassificationProviderRequest) -> DocumentClassificationProviderResult:
        text = f"{request.filename} {request.raw_text}".lower()
        current_type = (request.current_document_type or "").strip().lower()

        if current_type and current_type not in {"unknown", "unclassified", "generic_document"}:
            predicted_type = current_type
            confidence = 0.99
        elif "passport" in text:
            predicted_type = "passport"
            confidence = 0.96
        elif "statement" in text or "account" in text or "balance" in text:
            predicted_type = "bank_statement"
            confidence = 0.91
        elif "invoice" in text:
            predicted_type = "invoice"
            confidence = 0.88
        else:
            predicted_type = "generic_document"
            confidence = 0.55

        evidence_refs = (
            EvidenceRef(
                document_id=request.document_id,
                page_number=1,
                text_anchor=request.raw_text[:120] or request.filename,
                metadata={"source": "placeholder_classification"},
            ),
        )
        return DocumentClassificationProviderResult(
            document_type=predicted_type,
            confidence_score=confidence,
            evidence_refs=evidence_refs,
            provider_name="placeholder_classification",
            classification_metadata={"mode": "placeholder", "filename": request.filename},
        )


class PlaceholderExtractionProvider(ExtractionProvider):
    def process(self, request: ExtractionProviderRequest) -> ExtractionProviderResult:
        text = request.raw_text.strip()
        payload: dict[str, object] = {"document_type": request.document_type}
        evidence_refs: list[EvidenceRef] = []

        document_number_match = re.search(
            r"(passport|document|id|account)\s*(number|no)?[:#\s-]*([A-Z0-9-]{6,20})",
            text,
            re.IGNORECASE,
        )
        if document_number_match:
            extracted_value = document_number_match.group(3)
            key = "account_number" if request.document_type == "bank_statement" else "document_number"
            payload[key] = extracted_value
            evidence_refs.append(
                EvidenceRef(
                    document_id=request.document_id,
                    page_number=1,
                    text_anchor=document_number_match.group(0),
                    extracted_value=extracted_value,
                    metadata={"field_name": key},
                )
            )

        full_name_match = re.search(r"name[:\s-]+([A-Za-z][A-Za-z\s]{2,60})", text, re.IGNORECASE)
        if full_name_match:
            full_name = " ".join(full_name_match.group(1).split())
            payload["full_name"] = full_name
            evidence_refs.append(
                EvidenceRef(
                    document_id=request.document_id,
                    page_number=1,
                    text_anchor=full_name_match.group(0),
                    extracted_value=full_name,
                    metadata={"field_name": "full_name"},
                )
            )

        amount_match = re.search(r"(amount|balance)[:\s-]*([0-9][0-9,]*(?:\.[0-9]{2})?)", text, re.IGNORECASE)
        if amount_match:
            payload["amount"] = amount_match.group(2)

        if text and len(payload) == 1:
            payload["text_excerpt"] = text[:120]

        confidence_score = 0.92 if len(payload) > 2 else 0.78 if len(payload) == 2 else 0.45
        return ExtractionProviderResult(
            schema_name=f"{request.document_type}_mvp",
            extracted_payload=payload if text else {},
            confidence_score=confidence_score if text else 0.0,
            evidence_refs=tuple(evidence_refs),
            provider_name="placeholder_extraction",
            model_version="placeholder-v1",
        )


class PlaceholderValidationRulesEngine(ValidationRulesEngine):
    def evaluate(self, request: ValidationRulesEngineRequest) -> ValidationRulesEngineResult:
        validation_findings: list[ValidationFindingResult] = []
        risk_findings: list[RiskFindingResult] = []
        compliance_findings: list[ComplianceFindingResult] = []
        requires_manual_review = False
        rationale_parts: list[str] = []

        for document in request.documents:
            validation_findings.extend(
                self._evaluate_validation_findings(
                    document=document,
                    minimum_ocr_confidence=request.minimum_ocr_confidence,
                    minimum_extraction_confidence=request.minimum_extraction_confidence,
                    rationale_parts=rationale_parts,
                )
            )
            compliance_findings.extend(self._evaluate_compliance_findings(document=document, rationale_parts=rationale_parts))
            risk_findings.extend(self._evaluate_risk_findings(document=document, rationale_parts=rationale_parts))

        requires_manual_review = bool(validation_findings or risk_findings or compliance_findings)
        if requires_manual_review:
            rationale = "; ".join(dict.fromkeys(rationale_parts)) or "Manual review is required due to validation findings."
            return ValidationRulesEngineResult(
                validation_findings=tuple(validation_findings),
                risk_findings=tuple(risk_findings),
                compliance_findings=tuple(compliance_findings),
                requires_manual_review=True,
                rationale=rationale,
                recommendation_reason_code="manual_review_required",
                recommendation_outcome=DecisionOutcome.REVIEW_REQUIRED,
            )

        return ValidationRulesEngineResult(
            requires_manual_review=False,
            rationale="Automated checks completed without blocking findings.",
            recommendation_reason_code="system_recommendation_ready",
            recommendation_outcome=DecisionOutcome.APPROVED,
        )

    def _evaluate_validation_findings(
        self,
        *,
        document: ValidationDocumentContext,
        minimum_ocr_confidence: float,
        minimum_extraction_confidence: float,
        rationale_parts: list[str],
    ) -> list[ValidationFindingResult]:
        findings: list[ValidationFindingResult] = []
        if not document.raw_text.strip():
            findings.append(
                ValidationFindingResult(
                    document_id=document.document_id,
                    extraction_result_id=document.extraction_result_id,
                    rule_code="ocr_empty_output",
                    message="OCR returned no readable text.",
                    severity=FindingSeverity.ERROR,
                )
            )
            rationale_parts.append("OCR output was empty.")

        if (document.ocr_confidence_score or 0.0) < minimum_ocr_confidence:
            findings.append(
                ValidationFindingResult(
                    document_id=document.document_id,
                    extraction_result_id=document.extraction_result_id,
                    rule_code="ocr_low_confidence",
                    message="OCR confidence fell below the operational threshold.",
                    severity=FindingSeverity.WARNING,
                )
            )
            rationale_parts.append("OCR confidence was below threshold.")

        if not document.extracted_payload:
            findings.append(
                ValidationFindingResult(
                    document_id=document.document_id,
                    extraction_result_id=document.extraction_result_id,
                    rule_code="extraction_empty_payload",
                    message="Extraction returned no structured fields.",
                    severity=FindingSeverity.ERROR,
                    evidence_refs=document.evidence_refs,
                )
            )
            rationale_parts.append("Structured extraction was empty.")

        if (document.extraction_confidence_score or 0.0) < minimum_extraction_confidence:
            findings.append(
                ValidationFindingResult(
                    document_id=document.document_id,
                    extraction_result_id=document.extraction_result_id,
                    rule_code="extraction_low_confidence",
                    message="Extraction confidence fell below the operational threshold.",
                    severity=FindingSeverity.WARNING,
                    evidence_refs=document.evidence_refs,
                )
            )
            rationale_parts.append("Extraction confidence was below threshold.")

        return findings

    def _evaluate_compliance_findings(
        self,
        *,
        document: ValidationDocumentContext,
        rationale_parts: list[str],
    ) -> list[ComplianceFindingResult]:
        findings: list[ComplianceFindingResult] = []
        if document.document_type in {"passport", "national_id", "id_card"} and "document_number" not in document.extracted_payload:
            findings.append(
                ComplianceFindingResult(
                    document_id=document.document_id,
                    extraction_result_id=document.extraction_result_id,
                    policy_code="identity_document_number_required",
                    message="Identity document number could not be extracted.",
                    severity=FindingSeverity.ERROR,
                    evidence_refs=document.evidence_refs,
                )
            )
            rationale_parts.append("Identity document number was missing.")

        if document.document_type == "bank_statement" and "account_number" not in document.extracted_payload:
            findings.append(
                ComplianceFindingResult(
                    document_id=document.document_id,
                    extraction_result_id=document.extraction_result_id,
                    policy_code="bank_statement_account_number_required",
                    message="Bank statement account number could not be extracted.",
                    severity=FindingSeverity.ERROR,
                    evidence_refs=document.evidence_refs,
                )
            )
            rationale_parts.append("Bank statement account number was missing.")

        return findings

    def _evaluate_risk_findings(
        self,
        *,
        document: ValidationDocumentContext,
        rationale_parts: list[str],
    ) -> list[RiskFindingResult]:
        lowered_text = document.raw_text.lower()
        if any(keyword in lowered_text for keyword in ("fraud", "sanction", "suspicious", "pep")):
            rationale_parts.append("Risk-sensitive terminology was detected.")
            return [
                RiskFindingResult(
                    document_id=document.document_id,
                    extraction_result_id=document.extraction_result_id,
                    risk_code="manual_risk_keyword_match",
                    message="Risk-sensitive terminology was detected in OCR text.",
                    risk_level=RiskLevel.HIGH,
                    evidence_refs=document.evidence_refs,
                )
            ]
        return []

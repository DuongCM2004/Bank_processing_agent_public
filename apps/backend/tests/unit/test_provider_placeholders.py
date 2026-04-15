from __future__ import annotations

from uuid import uuid4

from ops_agent.domain.shared.enums import DecisionOutcome, FindingSeverity
from ops_agent.domain.shared.evidence import EvidenceRef
from ops_agent.infrastructure.providers.interfaces import (
    DocumentClassificationProviderRequest,
    ExtractionProviderRequest,
    OCRProviderRequest,
    ValidationDocumentContext,
    ValidationRulesEngineRequest,
)
from ops_agent.infrastructure.providers.placeholder import (
    PlaceholderDocumentClassificationProvider,
    PlaceholderExtractionProvider,
    PlaceholderOCRProvider,
    PlaceholderValidationRulesEngine,
)


def test_placeholder_ocr_provider_returns_confidence_and_evidence() -> None:
    document_id = uuid4()
    provider = PlaceholderOCRProvider()

    result = provider.process(
        OCRProviderRequest(
            case_id=uuid4(),
            document_id=document_id,
            filename="passport.pdf",
            mime_type="application/pdf",
            content=b"Passport No: P1234567\nName: Alice Example",
        )
    )

    assert result.provider_name == "placeholder_ocr"
    assert result.confidence_score is not None and result.confidence_score > 0.9
    assert len(result.evidence_refs) == 1
    assert result.evidence_refs[0].document_id == document_id


def test_placeholder_document_classification_provider_infers_document_type() -> None:
    document_id = uuid4()
    provider = PlaceholderDocumentClassificationProvider()

    result = provider.process(
        DocumentClassificationProviderRequest(
            case_id=uuid4(),
            document_id=document_id,
            filename="statement.pdf",
            mime_type="application/pdf",
            current_document_type="unknown",
            raw_text="Monthly statement account balance 1000.00",
            metadata={},
        )
    )

    assert result.document_type == "bank_statement"
    assert result.confidence_score is not None and result.confidence_score > 0.8
    assert len(result.evidence_refs) == 1
    assert result.evidence_refs[0].document_id == document_id


def test_placeholder_extraction_provider_returns_evidence_backed_payload() -> None:
    document_id = uuid4()
    provider = PlaceholderExtractionProvider()

    result = provider.process(
        ExtractionProviderRequest(
            case_id=uuid4(),
            document_id=document_id,
            document_type="passport",
            filename="passport.pdf",
            raw_text="Passport No: P1234567\nName: Alice Example",
        )
    )

    assert result.schema_name == "passport_mvp"
    assert result.extracted_payload["document_number"] == "P1234567"
    assert len(result.evidence_refs) >= 1
    assert all(isinstance(evidence, EvidenceRef) for evidence in result.evidence_refs)


def test_placeholder_validation_rules_engine_returns_structured_findings() -> None:
    provider = PlaceholderValidationRulesEngine()
    document_id = uuid4()
    extraction_result_id = uuid4()

    result = provider.evaluate(
        ValidationRulesEngineRequest(
            case_id=uuid4(),
            documents=(
                ValidationDocumentContext(
                    document_id=document_id,
                    extraction_result_id=extraction_result_id,
                    document_type="bank_statement",
                    filename="statement.pdf",
                    raw_text="suspicious transaction noted",
                    ocr_confidence_score=0.6,
                    extracted_payload={"document_type": "bank_statement"},
                    extraction_confidence_score=0.5,
                    evidence_refs=(
                        EvidenceRef(
                            document_id=document_id,
                            page_number=1,
                            text_anchor="suspicious transaction",
                        ),
                    ),
                ),
            ),
            minimum_ocr_confidence=0.75,
            minimum_extraction_confidence=0.8,
        )
    )

    assert result.requires_manual_review is True
    assert result.recommendation_outcome == DecisionOutcome.REVIEW_REQUIRED
    assert any(finding.severity == FindingSeverity.WARNING for finding in result.validation_findings)
    assert len(result.compliance_findings) == 1
    assert len(result.risk_findings) == 1

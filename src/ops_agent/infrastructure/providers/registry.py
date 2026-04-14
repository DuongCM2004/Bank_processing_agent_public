from __future__ import annotations

from dataclasses import dataclass

from ops_agent.infrastructure.providers.base import (
    DecisionProvider,
    DocumentClassifierProvider,
    FieldExtractorProvider,
    OCRProvider,
    ValidationProvider,
)


@dataclass(slots=True)
class ProviderRegistry:
    ocr: OCRProvider | None = None
    classifier: DocumentClassifierProvider | None = None
    extractor: FieldExtractorProvider | None = None
    validator: ValidationProvider | None = None
    decisioner: DecisionProvider | None = None

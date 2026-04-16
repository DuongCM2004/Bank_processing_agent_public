from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ProviderDocumentInput:
    document_id: UUID
    storage_key: str
    mime_type: str


@dataclass(frozen=True, slots=True)
class OCRProviderResult:
    raw_text: str
    confidence_score: float | None
    provider_job_id: str | None = None
    metadata: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ExtractionProviderResult:
    schema_name: str
    extracted_payload: dict[str, object]
    confidence_score: float | None
    evidence_refs: list[dict[str, object]]
    provider_job_id: str | None = None
    model_version: str | None = None


class OCRProvider(Protocol):
    provider_name: str

    def run_ocr(self, document: ProviderDocumentInput) -> OCRProviderResult:
        """Run OCR for a document and return traceable provider output."""


class ExtractionProvider(Protocol):
    provider_name: str

    def extract(self, document: ProviderDocumentInput, raw_text: str | None) -> ExtractionProviderResult:
        """Extract structured data while retaining field-level evidence links."""


class ValidationProvider(Protocol):
    provider_name: str

    def validate(self, payload: dict[str, object]) -> list[dict[str, object]]:
        """Validate extracted payload and return explicit findings."""


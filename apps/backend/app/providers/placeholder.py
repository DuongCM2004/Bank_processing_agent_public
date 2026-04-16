from __future__ import annotations

from app.core.exceptions import AppError
from app.providers.base import (
    ExtractionProviderResult,
    OCRProviderResult,
    ProviderDocumentInput,
)


class ProviderNotConfiguredError(AppError):
    status_code = 501
    error_code = "provider_not_configured"


class PlaceholderOCRProvider:
    provider_name = "placeholder_ocr"

    def run_ocr(self, document: ProviderDocumentInput) -> OCRProviderResult:
        raise ProviderNotConfiguredError(
            f"OCR provider is not configured for document {document.document_id}.",
        )


class PlaceholderExtractionProvider:
    provider_name = "placeholder_extraction"

    def extract(self, document: ProviderDocumentInput, raw_text: str | None) -> ExtractionProviderResult:
        raise ProviderNotConfiguredError(
            f"Extraction provider is not configured for document {document.document_id}.",
        )


class PlaceholderValidationProvider:
    provider_name = "placeholder_validation"

    def validate(self, payload: dict[str, object]) -> list[dict[str, object]]:
        raise ProviderNotConfiguredError("Validation provider is not configured.")


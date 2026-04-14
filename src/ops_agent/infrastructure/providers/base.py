from __future__ import annotations

from typing import Protocol


class OCRProvider(Protocol):
    def submit(self, *, case_id: str, document_id: str, object_key: str) -> str: ...


class DocumentClassifierProvider(Protocol):
    def classify(self, *, case_id: str, document_id: str, artifact_id: str) -> dict[str, object]: ...


class FieldExtractorProvider(Protocol):
    def extract(self, *, case_id: str, document_id: str, schema_name: str, artifact_id: str) -> dict[str, object]: ...


class ValidationProvider(Protocol):
    def validate(self, *, case_id: str, document_id: str | None = None) -> dict[str, object]: ...


class DecisionProvider(Protocol):
    def decide(self, *, case_id: str) -> dict[str, object]: ...

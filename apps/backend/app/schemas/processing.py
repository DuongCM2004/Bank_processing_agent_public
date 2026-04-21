from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from app.models.enums import ProcessingStatus
from app.schemas.common import APIModel, EvidenceRef

IDENTITY_DOCUMENT_FIELD_NAMES = (
    "document_type",
    "full_name",
    "first_name",
    "last_name",
    "id_number",
    "document_number",
    "date_of_birth",
    "sex",
    "gender",
    "nationality",
    "place_of_birth",
    "issue_date",
    "expiry_date",
    "issuing_authority",
    "address",
    "raw_full_text",
)


class QueueProcessingRequest(APIModel):
    actor_id: str | None = Field(default=None, max_length=128)
    reason_code: str | None = Field(default="queued_for_processing", max_length=100)


class QueueProcessingResponse(APIModel):
    case_id: UUID
    status: str


class OCRResultResponse(APIModel):
    id: UUID
    document_id: UUID
    status: ProcessingStatus
    raw_text: str | None
    confidence_score: float | None
    provider_name: str
    processed_at: datetime | None


class IdentityDocumentExtraction(APIModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    document_type: str | None
    full_name: str | None
    first_name: str | None
    last_name: str | None
    id_number: str | None
    document_number: str | None
    date_of_birth: str | None
    sex: str | None
    gender: str | None
    nationality: str | None
    place_of_birth: str | None
    issue_date: str | None
    expiry_date: str | None
    issuing_authority: str | None
    address: str | None
    raw_full_text: str | None

    @field_validator("*", mode="before")
    @classmethod
    def normalize_unknown_values(cls, value: object) -> object:
        if isinstance(value, str) and value.strip().lower() in {"", "unknown", "n/a", "na", "null"}:
            return None
        return value


class ExtractionResultCreate(APIModel):
    document_id: UUID
    ocr_result_id: UUID | None = None
    schema_name: str = Field(default="identity-document-v1", max_length=120)
    extracted_payload: IdentityDocumentExtraction
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    provider_name: str = Field(default="openai_responses_gpt", max_length=100)
    model_version: str | None = Field(default="gpt-4.1", max_length=100)


class ExtractionResultResponse(APIModel):
    id: UUID
    document_id: UUID
    status: ProcessingStatus
    schema_name: str
    extracted_payload: dict[str, object]
    confidence_score: float | None
    evidence_refs: list[dict[str, object]]
    provider_name: str
    model_version: str | None
    processed_at: datetime | None

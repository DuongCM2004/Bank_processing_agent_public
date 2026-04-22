from __future__ import annotations

import base64
import io
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from PIL import Image, ImageOps

from ops_agent.config import AIIntegrationSettings
from ops_agent.domain.shared.exceptions import OpsAgentError
from ops_agent.infrastructure.providers.interfaces import (
    ExtractionProvider,
    ExtractionProviderRequest,
    ExtractionProviderResult,
    OCRProvider,
    OCRProviderRequest,
    OCRProviderResult,
)


TARGET_FIELDS = (
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

ID_CARD_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {field_name: {"type": ["string", "null"]} for field_name in TARGET_FIELDS},
    "required": list(TARGET_FIELDS),
    "additionalProperties": False,
}

SYSTEM_PROMPT = """
You extract information from identity-card-like images.

Rules:
1. Return only the JSON object defined by the schema.
2. If the image is not an ID card or does not clearly contain a field, return null for that field.
3. Preserve visible text exactly when possible.
4. Do not hallucinate.
5. Set document_type to the best short label you can infer from the image, such as:
   "national_id", "passport", "driver_license", "resident_card", or null.
6. raw_full_text should be a best-effort plain-text transcription of visible document text.
7. If a field is uncertain, use null.
""".strip()

RETRY_PROMPT = """
You are re-running extraction because the previous output failed validation.

Return exactly the schema.
Use null for anything uncertain.
Do not include explanations.
Keep values literal and compact.
""".strip()


class ExtractState(TypedDict):
    image_data_url: str
    prediction: NotRequired[dict[str, str | None]]
    is_valid: NotRequired[bool]
    validation_errors: NotRequired[list[str]]
    attempts: int
    status: str


@dataclass(frozen=True, slots=True)
class OpenAIExtractionConfig:
    api_key: str
    model: str
    store_response: bool
    timeout_seconds: int
    max_side_for_upload: int
    jpeg_quality: int
    schema_name: str
    prompt_version: str

    @classmethod
    def from_settings(cls, settings: AIIntegrationSettings) -> OpenAIExtractionConfig:
        if not settings.openai_api_key:
            raise OpsAgentError(
                "OpenAI extraction is enabled but OPS_AGENT_OPENAI_API_KEY is not configured.",
                error_code="openai_api_key_missing",
                status_code=500,
            )
        return cls(
            api_key=settings.openai_api_key,
            model=settings.gpt_model,
            store_response=settings.openai_store_response,
            timeout_seconds=settings.provider_timeout_seconds,
            max_side_for_upload=settings.image_max_dimension_px,
            jpeg_quality=settings.image_jpeg_quality,
            schema_name=settings.llm_schema_version,
            prompt_version=settings.llm_prompt_version,
        )


class OpenAIVisionOCRProvider(OCRProvider):
    """Marks OCR as handled by the downstream vision extraction provider."""

    provider_name = "openai_vision_ocr_passthrough"

    def process(self, request: OCRProviderRequest) -> OCRProviderResult:
        return OCRProviderResult(
            raw_text="",
            confidence_score=1.0,
            provider_name=self.provider_name,
            page_count=1,
            result_metadata={"mode": "vision_extraction", "filename": request.filename},
        )


class OpenAIIdentityExtractionProvider(ExtractionProvider):
    provider_name = "openai_responses_gpt"

    def __init__(self, settings: AIIntegrationSettings) -> None:
        self._config = OpenAIExtractionConfig.from_settings(settings)

    def process(self, request: ExtractionProviderRequest) -> ExtractionProviderResult:
        if request.content is None:
            raise OpsAgentError(
                "OpenAI extraction requires document bytes on ExtractionProviderRequest.",
                error_code="document_content_missing",
                status_code=500,
            )
        if request.mime_type not in {"image/png", "image/jpeg"}:
            raise OpsAgentError(
                "OpenAI image extraction supports image/png and image/jpeg, "
                f"got '{request.mime_type}'.",
                error_code="unsupported_openai_extraction_media_type",
                status_code=415,
            )

        image_data_url = image_bytes_to_data_url(
            request.content,
            max_side=self._config.max_side_for_upload,
            jpeg_quality=self._config.jpeg_quality,
        )
        graph = build_extraction_graph(
            lambda prompt: self._extract_from_image(image_data_url, prompt)
        )
        result = graph.invoke(
            {"image_data_url": image_data_url, "attempts": 0, "status": "init"},
            config={"configurable": {"thread_id": f"document-{request.document_id}"}},
        )

        prediction = result.get("prediction") or canonicalize_prediction({})
        is_valid, validation_errors = validate_prediction(prediction)
        if not is_valid:
            raise OpsAgentError(
                "OpenAI extraction failed strict schema validation after retry.",
                error_code="openai_extraction_schema_validation_failed",
                status_code=502,
            )

        return ExtractionProviderResult(
            schema_name=self._config.schema_name,
            extracted_payload=prediction,
            confidence_score=0.9,
            evidence_refs=(),
            provider_name=self.provider_name,
            model_version=self._config.model,
            provider_job_id=None,
        )

    def _extract_from_image(self, image_data_url: str, system_prompt: str) -> dict[str, str | None]:
        from openai import OpenAI

        client = OpenAI(api_key=self._config.api_key, timeout=self._config.timeout_seconds)
        response = client.responses.create(
            model=self._config.model,
            store=self._config.store_response,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Extract ID-card information from this image as JSON.",
                        },
                        {"type": "input_image", "image_url": image_data_url},
                    ],
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "id_card_extraction",
                    "schema": ID_CARD_SCHEMA,
                    "strict": True,
                }
            },
        )
        return canonicalize_prediction(json.loads(response.output_text))


def safe_open_image(content: bytes) -> Image.Image | None:
    try:
        image = Image.open(io.BytesIO(content))
        return ImageOps.exif_transpose(image).convert("RGB")
    except Exception:
        return None


def resize_for_upload(image: Image.Image, max_side: int = 1600) -> Image.Image:
    width, height = image.size
    longest = max(width, height)
    if longest <= max_side:
        return image

    scale = max_side / longest
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return image.resize(new_size)


def image_bytes_to_data_url(content: bytes, *, max_side: int = 1600, jpeg_quality: int = 90) -> str:
    image = safe_open_image(content)
    if image is None:
        raise OpsAgentError(
            "Cannot open uploaded document as an image.",
            error_code="image_preprocessing_failed",
            status_code=415,
        )

    image = resize_for_upload(image, max_side=max_side)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=jpeg_quality)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def canonicalize_prediction(prediction: dict[str, Any]) -> dict[str, str | None]:
    output: dict[str, str | None] = {}
    for field_name in TARGET_FIELDS:
        value = prediction.get(field_name)
        if value is None:
            output[field_name] = None
            continue
        normalized = str(value).replace("\u00a0", " ").strip()
        output[field_name] = normalized if normalized else None
    return output


def validate_prediction(prediction: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not isinstance(prediction, dict):
        return False, ["prediction_not_dict"]
    if set(prediction.keys()) != set(TARGET_FIELDS):
        errors.append("schema_keys_mismatch")
    for field_name in TARGET_FIELDS:
        value = prediction.get(field_name)
        if value is not None and not isinstance(value, str):
            errors.append(f"{field_name}:not_string_or_null")
    for field_name, value in prediction.items():
        if value is not None and len(value) > 5000:
            errors.append(f"{field_name}:too_long")
    return len(errors) == 0, errors


def build_extraction_graph(extract: Callable[[str], dict[str, str | None]]):
    def node_extract(state: ExtractState) -> dict[str, Any]:
        prediction = extract(SYSTEM_PROMPT)
        return {
            "prediction": prediction,
            "attempts": state.get("attempts", 0) + 1,
            "status": "extracted",
        }

    def node_validate(state: ExtractState) -> dict[str, Any]:
        ok, errors = validate_prediction(state.get("prediction") or {})
        return {"is_valid": ok, "validation_errors": errors, "status": "validated"}

    def node_retry(state: ExtractState) -> dict[str, Any]:
        prediction = extract(RETRY_PROMPT)
        return {
            "prediction": prediction,
            "attempts": state.get("attempts", 0) + 1,
            "status": "retry_extracted",
        }

    def route_after_validate(state: ExtractState) -> str:
        if state.get("is_valid", False):
            return "done"
        if state.get("attempts", 0) < 2:
            return "retry"
        return "done"

    builder = StateGraph(ExtractState)
    builder.add_node("extract", node_extract)
    builder.add_node("validate", node_validate)
    builder.add_node("retry", node_retry)
    builder.add_edge(START, "extract")
    builder.add_edge("extract", "validate")
    builder.add_conditional_edges("validate", route_after_validate, {"retry": "retry", "done": END})
    builder.add_edge("retry", "validate")
    return builder.compile(checkpointer=InMemorySaver())

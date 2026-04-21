from __future__ import annotations

import base64
import json
from io import BytesIO
from typing import Any

from PIL import Image, ImageOps

from app.core.config import Settings
from app.pipelines.llm_extraction import build_identity_extraction_graph
from app.providers.base import ExtractionProviderResult, ProviderDocumentInput
from app.providers.placeholder import ProviderNotConfiguredError
from app.schemas.processing import IDENTITY_DOCUMENT_FIELD_NAMES


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


class GptDocumentExtractionProvider:
    provider_name = "openai_responses_gpt"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def extract(self, document: ProviderDocumentInput, raw_text: str | None) -> ExtractionProviderResult:
        del raw_text
        if not self.settings.openai_api_key:
            raise ProviderNotConfiguredError(
                "OPENAI_API_KEY is not configured. Set OPS_AGENT_OPENAI_API_KEY before running extraction."
            )

        image_data_url = self._image_to_data_url(document)
        graph = build_identity_extraction_graph(self._call_gpt)
        result = graph.invoke({"image_data_url": image_data_url, "attempt_count": 0})
        if result.get("validation_error"):
            raise ProviderNotConfiguredError(f"LLM extraction failed schema validation: {result['validation_error']}")

        return ExtractionProviderResult(
            schema_name=self.settings.llm_schema_version,
            extracted_payload=result["normalized_output"],
            confidence_score=None,
            evidence_refs=[
                {
                    "document_id": str(document.document_id),
                    "metadata": {
                        "provider": self.provider_name,
                        "prompt_version": self.settings.llm_prompt_version,
                        "schema_version": self.settings.llm_schema_version,
                    },
                }
            ],
            model_version=self.settings.gpt_model,
        )

    def _image_to_data_url(self, document: ProviderDocumentInput) -> str:
        if document.mime_type not in {"image/png", "image/jpeg"}:
            raise ProviderNotConfiguredError(
                f"Notebook-style GPT extraction expects an image upload, got {document.mime_type}."
            )

        source_path = self.settings.storage_root_path / document.storage_key
        try:
            with Image.open(source_path) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                image = self._resize_for_upload(image)
                buffer = BytesIO()
                image.save(buffer, format="JPEG", quality=self.settings.image_jpeg_quality)
        except Exception as exc:
            raise ProviderNotConfiguredError(f"Uploaded document cannot be opened as an image: {exc}") from exc

        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"

    def _resize_for_upload(self, image: Image.Image) -> Image.Image:
        width, height = image.size
        longest = max(width, height)
        if longest <= self.settings.image_max_dimension_px:
            return image

        scale = self.settings.image_max_dimension_px / longest
        new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        return image.resize(new_size)

    def _call_gpt(self, image_data_url: str, retry_prompt: bool, schema: dict[str, Any]) -> dict[str, Any]:
        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key, timeout=self.settings.ai_provider_timeout_seconds)
        response = client.responses.create(
            model=self.settings.gpt_model,
            store=self.settings.openai_store_response,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": RETRY_PROMPT if retry_prompt else SYSTEM_PROMPT}],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "Extract ID-card information from this image as JSON."},
                        {"type": "input_image", "image_url": image_data_url},
                    ],
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "id_card_extraction_retry" if retry_prompt else "id_card_extraction",
                    "schema": schema,
                    "strict": True,
                }
            },
        )
        return self._canonicalize_prediction(json.loads(response.output_text))

    @staticmethod
    def _canonicalize_prediction(prediction: dict[str, Any]) -> dict[str, str | None]:
        output: dict[str, str | None] = {}
        for field_name in IDENTITY_DOCUMENT_FIELD_NAMES:
            value = prediction.get(field_name)
            if value is None:
                output[field_name] = None
                continue
            normalized = str(value).replace("\u00a0", " ").strip()
            output[field_name] = normalized if normalized else None
        return output

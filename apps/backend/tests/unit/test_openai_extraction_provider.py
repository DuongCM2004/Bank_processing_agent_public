from __future__ import annotations

from io import BytesIO
from uuid import uuid4

from PIL import Image

from ops_agent.config import AIIntegrationSettings
from ops_agent.infrastructure.providers.interfaces import (
    ExtractionProviderRequest,
    OCRProviderRequest,
)
from ops_agent.infrastructure.providers.openai_extraction import (
    OpenAIIdentityExtractionProvider,
    OpenAIVisionOCRProvider,
    SYSTEM_PROMPT,
    TARGET_FIELDS,
    canonicalize_prediction,
    image_bytes_to_data_url,
    validate_prediction,
)


def _png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (20, 10), color=(255, 255, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


class StubOpenAIIdentityExtractionProvider(OpenAIIdentityExtractionProvider):
    def __init__(self) -> None:
        super().__init__(
            AIIntegrationSettings(
                provider_mode="gpt",
                openai_api_key="test-key",
                gpt_model="gpt-test",
            )
        )
        self.prompts: list[str] = []

    def _extract_from_image(self, image_data_url: str, system_prompt: str) -> dict[str, str | None]:
        assert image_data_url.startswith("data:image/jpeg;base64,")
        self.prompts.append(system_prompt)
        if len(self.prompts) == 1:
            return {"document_type": "national_id"}
        return canonicalize_prediction(
            {
                "document_type": "national_id",
                "full_name": "  Alice Example  ",
                "document_number": "A1234567",
                "raw_full_text": "National ID Alice Example A1234567",
            }
        )


def test_image_bytes_to_data_url_resizes_and_encodes_image() -> None:
    data_url = image_bytes_to_data_url(_png_bytes(), max_side=8, jpeg_quality=80)

    assert data_url.startswith("data:image/jpeg;base64,")


def test_canonicalize_and_validate_prediction_enforce_target_schema() -> None:
    prediction = canonicalize_prediction({"full_name": " Alice\u00a0Example ", "document_type": ""})
    ok, errors = validate_prediction(prediction)

    assert ok is True
    assert errors == []
    assert set(prediction) == set(TARGET_FIELDS)
    assert prediction["full_name"] == "Alice Example"
    assert prediction["document_type"] is None


def test_openai_identity_provider_retries_once_and_returns_structured_payload() -> None:
    provider = StubOpenAIIdentityExtractionProvider()
    result = provider.process(
        ExtractionProviderRequest(
            case_id=uuid4(),
            document_id=uuid4(),
            document_type="unknown",
            filename="id-card.png",
            raw_text="",
            mime_type="image/png",
            content=_png_bytes(),
        )
    )

    assert result.provider_name == "openai_responses_gpt"
    assert result.model_version == "gpt-test"
    assert result.schema_name == "identity-document-v1"
    assert result.extracted_payload["full_name"] == "Alice Example"
    assert result.extracted_payload["document_number"] == "A1234567"
    assert len(provider.prompts) == 2
    assert provider.prompts[0] == SYSTEM_PROMPT


def test_openai_vision_ocr_provider_marks_ocr_as_passthrough() -> None:
    provider = OpenAIVisionOCRProvider()
    result = provider.process(
        OCRProviderRequest(
            case_id=uuid4(),
            document_id=uuid4(),
            filename="id-card.png",
            mime_type="image/png",
            content=_png_bytes(),
        )
    )

    assert result.provider_name == "openai_vision_ocr_passthrough"
    assert result.raw_text == ""
    assert result.confidence_score == 1.0

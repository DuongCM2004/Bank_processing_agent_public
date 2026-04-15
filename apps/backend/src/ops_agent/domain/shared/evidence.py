from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(slots=True, kw_only=True)
class EvidenceRef:
    """Traceable evidence pointer back to the originating document."""

    document_id: UUID
    page_number: int | None = None
    text_anchor: str | None = None
    bounding_box: dict[str, float] | None = None
    extracted_value: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def to_record(self) -> dict[str, object]:
        return {
            "document_id": str(self.document_id),
            "page_number": self.page_number,
            "text_anchor": self.text_anchor,
            "bounding_box": self.bounding_box,
            "extracted_value": self.extracted_value,
            "metadata": self.metadata,
        }

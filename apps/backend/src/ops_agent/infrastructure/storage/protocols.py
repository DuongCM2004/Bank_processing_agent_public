from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class StoredDocument:
    storage_key: str
    absolute_path: Path
    size_bytes: int
    sha256_digest: str


@dataclass(frozen=True, slots=True)
class RetrievedDocument:
    storage_key: str
    absolute_path: Path
    size_bytes: int


class DocumentStorage(Protocol):
    def store(
        self,
        *,
        case_id: UUID,
        document_id: UUID,
        filename: str,
        content: bytes,
    ) -> StoredDocument:
        """Persist content and return a traceable storage result."""

    def resolve(self, *, storage_key: str) -> RetrievedDocument:
        """Resolve a stored document to a safe local file reference."""

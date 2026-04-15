from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import UUID

from ops_agent.infrastructure.storage.protocols import DocumentStorage, RetrievedDocument, StoredDocument


class LocalDocumentStorage(DocumentStorage):
    def __init__(self, root_path: Path) -> None:
        self._root_path = root_path
        self._resolved_root_path = root_path.resolve()

    def store(
        self,
        *,
        case_id: UUID,
        document_id: UUID,
        filename: str,
        content: bytes,
    ) -> StoredDocument:
        safe_filename = _sanitize_filename(filename)
        relative_path = Path(f"cases/{case_id}/documents/{document_id}/{safe_filename}")
        absolute_path = (self._root_path / relative_path).resolve()
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(content)

        sha256_digest = hashlib.sha256(content).hexdigest()
        return StoredDocument(
            storage_key=relative_path.as_posix(),
            absolute_path=absolute_path,
            size_bytes=len(content),
            sha256_digest=sha256_digest,
        )

    def resolve(self, *, storage_key: str) -> RetrievedDocument:
        relative_path = Path(storage_key)
        absolute_path = (self._root_path / relative_path).resolve()
        if absolute_path != self._resolved_root_path and self._resolved_root_path not in absolute_path.parents:
            raise ValueError(f"Storage key '{storage_key}' resolves outside the configured root path.")
        if not absolute_path.exists() or not absolute_path.is_file():
            raise FileNotFoundError(storage_key)

        return RetrievedDocument(
            storage_key=storage_key,
            absolute_path=absolute_path,
            size_bytes=absolute_path.stat().st_size,
        )


def _sanitize_filename(filename: str) -> str:
    cleaned = "".join(character if character.isalnum() or character in {".", "-", "_"} else "_" for character in filename)
    return cleaned or "upload.bin"

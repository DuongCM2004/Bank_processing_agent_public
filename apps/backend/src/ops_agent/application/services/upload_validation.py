from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from fastapi import UploadFile

from ops_agent.config import StorageSettings
from ops_agent.domain.shared.exceptions import ConflictError, PayloadTooLargeError, UnsupportedMediaTypeError


class InvalidUploadFilenameError(ConflictError):
    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="invalid_upload_filename")


class EmptyUploadError(ConflictError):
    def __init__(self) -> None:
        super().__init__("Uploaded file must not be empty.", error_code="empty_upload")


@dataclass(frozen=True, slots=True)
class ValidatedUpload:
    original_filename: str
    sanitized_filename: str
    mime_type: str
    size_bytes: int


_SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")
_REPEATED_SEPARATOR_PATTERN = re.compile(r"_{2,}")
_MAX_FILENAME_LENGTH = 180


def validate_upload_file(
    *,
    upload: UploadFile,
    content: bytes,
    storage_settings: StorageSettings,
) -> ValidatedUpload:
    original_filename = _require_filename(upload.filename)
    sanitized_filename = sanitize_upload_filename(original_filename)
    mime_type = normalize_mime_type(upload.content_type)

    if mime_type not in storage_settings.allowed_mime_types:
        raise UnsupportedMediaTypeError(
            f"File type '{mime_type}' is not allowed. Allowed types: "
            f"{', '.join(storage_settings.allowed_mime_types)}."
        )

    size_bytes = len(content)
    if size_bytes == 0:
        raise EmptyUploadError()
    if size_bytes > storage_settings.max_upload_bytes:
        raise PayloadTooLargeError(
            f"Uploaded file exceeds the maximum allowed size of {storage_settings.max_upload_bytes} bytes."
        )

    return ValidatedUpload(
        original_filename=original_filename,
        sanitized_filename=sanitized_filename,
        mime_type=mime_type,
        size_bytes=size_bytes,
    )


def normalize_mime_type(content_type: str | None) -> str:
    return (content_type or "application/octet-stream").split(";", maxsplit=1)[0].strip().lower()


def sanitize_upload_filename(filename: str) -> str:
    original_filename = _require_filename(filename)
    if "/" in original_filename or "\\" in original_filename:
        raise InvalidUploadFilenameError("Uploaded filename must not contain path separators.")

    normalized = unicodedata.normalize("NFKC", original_filename).strip()
    if any(unicodedata.category(character).startswith("C") for character in normalized):
        raise InvalidUploadFilenameError("Uploaded filename must not contain control characters.")

    sanitized = _SAFE_FILENAME_PATTERN.sub("_", normalized)
    sanitized = _REPEATED_SEPARATOR_PATTERN.sub("_", sanitized).strip("._-")

    if not sanitized:
        raise InvalidUploadFilenameError("Uploaded filename does not contain any safe characters.")

    if "." not in sanitized and "." in normalized:
        sanitized = f"{sanitized}.bin"

    return sanitized[:_MAX_FILENAME_LENGTH]


def _require_filename(filename: str | None) -> str:
    if not filename or not filename.strip():
        raise InvalidUploadFilenameError("Uploaded file must include a filename.")
    return filename.strip()

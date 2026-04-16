from __future__ import annotations

from types import SimpleNamespace

import pytest

from ops_agent.config import StorageSettings
from ops_agent.application.services.upload_validation import (
    EmptyUploadError,
    InvalidUploadFilenameError,
    sanitize_upload_filename,
    validate_upload_file,
)
from ops_agent.domain.shared.exceptions import PayloadTooLargeError, UnsupportedMediaTypeError


def _upload(filename: str, content_type: str):
    return SimpleNamespace(filename=filename, content_type=content_type)


def test_validate_upload_file_normalizes_mime_and_sanitizes_filename() -> None:
    result = validate_upload_file(
        upload=_upload("bank statement (Q1).PDF", "Application/PDF; charset=binary"),
        content=b"pdf-content",
        storage_settings=StorageSettings(max_upload_bytes=1024),
    )

    assert result.original_filename == "bank statement (Q1).PDF"
    assert result.sanitized_filename == "bank_statement_Q1_.PDF"
    assert result.mime_type == "application/pdf"
    assert result.size_bytes == len(b"pdf-content")


def test_sanitize_upload_filename_rejects_path_components() -> None:
    with pytest.raises(InvalidUploadFilenameError) as exc_info:
        sanitize_upload_filename("../passport.pdf")

    assert exc_info.value.error_code == "invalid_upload_filename"


def test_validate_upload_file_rejects_disallowed_mime_type() -> None:
    with pytest.raises(UnsupportedMediaTypeError) as exc_info:
        validate_upload_file(
            upload=_upload("statement.txt", "text/plain"),
            content=b"plain text",
            storage_settings=StorageSettings(max_upload_bytes=1024),
        )

    assert exc_info.value.error_code == "unsupported_media_type"


def test_validate_upload_file_rejects_empty_upload() -> None:
    with pytest.raises(EmptyUploadError) as exc_info:
        validate_upload_file(
            upload=_upload("empty.pdf", "application/pdf"),
            content=b"",
            storage_settings=StorageSettings(max_upload_bytes=1024),
        )

    assert exc_info.value.error_code == "empty_upload"


def test_validate_upload_file_rejects_oversized_upload() -> None:
    with pytest.raises(PayloadTooLargeError) as exc_info:
        validate_upload_file(
            upload=_upload("large.pdf", "application/pdf"),
            content=b"x" * 1025,
            storage_settings=StorageSettings(max_upload_bytes=1024),
        )

    assert exc_info.value.error_code == "payload_too_large"

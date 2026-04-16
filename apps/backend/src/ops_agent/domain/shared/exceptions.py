from __future__ import annotations


class OpsAgentError(Exception):
    """Base application exception with a stable public code."""

    def __init__(self, message: str, *, error_code: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code


class ResourceNotFoundError(OpsAgentError):
    def __init__(self, resource_type: str, resource_id: str) -> None:
        super().__init__(
            f"{resource_type} '{resource_id}' was not found.",
            error_code="resource_not_found",
            status_code=404,
        )


class ConflictError(OpsAgentError):
    def __init__(self, message: str, *, error_code: str = "conflict") -> None:
        super().__init__(message, error_code=error_code, status_code=409)


class AuthenticationRequiredError(OpsAgentError):
    def __init__(self) -> None:
        super().__init__(
            "Authentication is required for this operation.",
            error_code="authentication_required",
            status_code=401,
        )


class AuthorizationError(OpsAgentError):
    def __init__(self, message: str = "The authenticated principal is not authorized for this operation.") -> None:
        super().__init__(message, error_code="permission_denied", status_code=403)


class PayloadTooLargeError(OpsAgentError):
    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="payload_too_large", status_code=413)


class UnsupportedMediaTypeError(OpsAgentError):
    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="unsupported_media_type", status_code=415)


class DocumentContentUnavailableError(OpsAgentError):
    def __init__(self, document_id: str) -> None:
        super().__init__(
            f"Stored content for document '{document_id}' is unavailable.",
            error_code="document_content_unavailable",
            status_code=409,
        )


class CaseProcessingExecutionError(OpsAgentError):
    def __init__(self, case_id: str) -> None:
        super().__init__(
            f"Case '{case_id}' processing failed.",
            error_code="case_processing_failed",
            status_code=500,
        )

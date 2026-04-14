from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DomainError(Exception):
    error_code: str
    message: str
    status_code: int
    retryable: bool = False
    details: dict[str, object] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


class ResourceNotFoundError(DomainError):
    def __init__(self, error_code: str, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(error_code=error_code, message=message, status_code=404, details=details or {})


class ConflictError(DomainError):
    def __init__(self, error_code: str, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(error_code=error_code, message=message, status_code=409, details=details or {})


class ValidationDomainError(DomainError):
    def __init__(self, error_code: str, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(error_code=error_code, message=message, status_code=422, details=details or {})

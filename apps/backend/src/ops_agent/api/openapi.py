from __future__ import annotations

from collections.abc import Iterable

from ops_agent.api.schemas import ErrorEnvelope

API_DESCRIPTION = (
    "REST API for the banking-grade Document Processing Agent MVP. "
    "Endpoints are organized by operational domain and return stable, structured responses for frontend case review workflows."
)

OPENAPI_TAGS = [
    {
        "name": "health",
        "description": "System health and readiness endpoints for service monitoring.",
    },
    {
        "name": "cases",
        "description": "Case intake, listing, detail retrieval, and explicit case workflow state transitions.",
    },
    {
        "name": "documents",
        "description": "Document upload, metadata retrieval, listing, and controlled content download for a case.",
    },
    {
        "name": "manual-review",
        "description": "Manual review actions, reviewer notes, corrections, and controlled case resubmission.",
    },
    {
        "name": "decisions",
        "description": "Explicit decision recording, approval, rejection, and additional-review requests.",
    },
    {
        "name": "audit-events",
        "description": "Structured audit trail retrieval for compliance review and operational traceability.",
    },
]

ERROR_SPECS: dict[int, tuple[str, str, str]] = {
    400: ("Bad Request", "bad_request", "The request could not be processed."),
    401: ("Unauthorized", "authentication_required", "Authentication is required for this operation."),
    403: ("Forbidden", "permission_denied", "The authenticated principal is not authorized for this operation."),
    404: ("Not Found", "resource_not_found", "The requested resource was not found."),
    409: ("Conflict", "conflict", "The request conflicts with the current resource state."),
    413: ("Payload Too Large", "payload_too_large", "The uploaded payload exceeds the configured size limit."),
    415: ("Unsupported Media Type", "unsupported_media_type", "The supplied media type is not supported."),
    422: ("Validation Error", "request_validation_failed", "Request validation failed."),
    500: ("Internal Server Error", "internal_server_error", "An unexpected error occurred."),
}


def error_responses(*status_codes: int) -> dict[int, dict[str, object]]:
    responses: dict[int, dict[str, object]] = {}
    for status_code in status_codes:
        title, code, message = ERROR_SPECS[status_code]
        response_entry: dict[str, object] = {
            "model": ErrorEnvelope,
            "description": title,
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": code,
                            "message": message,
                            "trace_id": None,
                            "details": [],
                        }
                    }
                }
            },
        }
        if status_code == 422:
            response_entry["content"] = {
                "application/json": {
                    "example": {
                        "error": {
                            "code": code,
                            "message": message,
                            "trace_id": None,
                            "details": [
                                {
                                    "field": "body.documents.0.filename",
                                    "issue": "Field required",
                                    "context": {},
                                }
                            ],
                        }
                    }
                }
            }
        responses[status_code] = response_entry
    return responses


def merge_responses(*response_maps: dict[int, dict[str, object]]) -> dict[int, dict[str, object]]:
    merged: dict[int, dict[str, object]] = {}
    for response_map in response_maps:
        merged.update(response_map)
    return merged


def ensure_unique_tags(tags: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for tag in tags:
        if tag not in seen:
            ordered.append(tag)
            seen.add(tag)
    return ordered

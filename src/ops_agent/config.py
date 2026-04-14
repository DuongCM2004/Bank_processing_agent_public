from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AppSettings:
    app_name: str = "bank-document-processing-agent"
    environment: str = "local"
    api_version: str = "v1"
    database_url: str = "postgresql://ops_agent:ops_agent@localhost:5432/ops_agent"
    object_store_bucket: str = "ops-agent-artifacts"
    temporal_namespace: str = "ops-agent"
    keycloak_issuer_url: str = "http://localhost:8080/realms/ops-agent"
    oidc_audience: str = "ops-agent-api"
    jwks_cache_ttl_seconds: int = 900
    audit_log_level: str = "INFO"
    review_queue_default: str = "ops_review"
    prompt_registry_version: str = "2026-04-14"
    max_upload_bytes: int = 25_000_000
    allowed_upload_mime_types: str = "application/pdf,image/png,image/jpeg"
    presigned_url_ttl_seconds: int = 300
    storage_kms_key_id: str = "local-dev-kms-key"
    service_auth_audience: str = "ops-agent-internal"

    @classmethod
    def from_env(cls) -> "AppSettings":
        defaults = cls()
        return cls(
            app_name=os.getenv("OPS_AGENT_APP_NAME", defaults.app_name),
            environment=os.getenv("OPS_AGENT_ENV", defaults.environment),
            api_version=os.getenv("OPS_AGENT_API_VERSION", defaults.api_version),
            database_url=os.getenv("OPS_AGENT_DATABASE_URL", defaults.database_url),
            object_store_bucket=os.getenv("OPS_AGENT_OBJECT_STORE_BUCKET", defaults.object_store_bucket),
            temporal_namespace=os.getenv("OPS_AGENT_TEMPORAL_NAMESPACE", defaults.temporal_namespace),
            keycloak_issuer_url=os.getenv("OPS_AGENT_KEYCLOAK_ISSUER_URL", defaults.keycloak_issuer_url),
            oidc_audience=os.getenv("OPS_AGENT_OIDC_AUDIENCE", defaults.oidc_audience),
            jwks_cache_ttl_seconds=int(
                os.getenv("OPS_AGENT_JWKS_CACHE_TTL_SECONDS", str(defaults.jwks_cache_ttl_seconds))
            ),
            audit_log_level=os.getenv("OPS_AGENT_AUDIT_LOG_LEVEL", defaults.audit_log_level),
            review_queue_default=os.getenv("OPS_AGENT_REVIEW_QUEUE_DEFAULT", defaults.review_queue_default),
            prompt_registry_version=os.getenv("OPS_AGENT_PROMPT_REGISTRY_VERSION", defaults.prompt_registry_version),
            max_upload_bytes=int(os.getenv("OPS_AGENT_MAX_UPLOAD_BYTES", str(defaults.max_upload_bytes))),
            allowed_upload_mime_types=os.getenv("OPS_AGENT_ALLOWED_UPLOAD_MIME_TYPES", defaults.allowed_upload_mime_types),
            presigned_url_ttl_seconds=int(
                os.getenv("OPS_AGENT_PRESIGNED_URL_TTL_SECONDS", str(defaults.presigned_url_ttl_seconds))
            ),
            storage_kms_key_id=os.getenv("OPS_AGENT_STORAGE_KMS_KEY_ID", defaults.storage_kms_key_id),
            service_auth_audience=os.getenv("OPS_AGENT_SERVICE_AUTH_AUDIENCE", defaults.service_auth_audience),
        )

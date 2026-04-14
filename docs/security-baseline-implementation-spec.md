# Security Baseline Implementation Specification

This specification defines the MVP security baseline for the banking Document Processing Agent (Ops Agent). It is aligned to [config.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/config.py), [security_baseline.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/security_baseline.py), [.env.example](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/.env.example), and the existing workflow and audit contracts.

## Scope

This baseline is practical and build-oriented. It is intended to protect sensitive banking documents in the MVP without pretending that all later hardening is already complete.

Core principles:

- default deny
- explicit role checks on every mutating action
- no direct public access to stored documents
- encryption in transit and at rest
- secrets never committed to the repository
- audit trail protection is mandatory

## 1. Auth Model Assumptions

MVP auth model:

- external users authenticate through an OIDC provider
- backend APIs accept bearer JWTs only
- internal worker and service calls use separate service identities
- browser sessions do not call internal workflow endpoints directly

Implementation assumptions:

- IdP: Keycloak or bank-approved OIDC provider
- issuer URL configured via `OPS_AGENT_KEYCLOAK_ISSUER_URL`
- audience validation configured via `OPS_AGENT_OIDC_AUDIENCE`
- JWKS cache TTL configured via `OPS_AGENT_JWKS_CACHE_TTL_SECONDS`

Required token checks:

- signature valid
- issuer exact match
- audience exact match
- token not expired
- token contains subject and role claims
- service tokens distinguished from user tokens by audience or dedicated claim

Explicit build control:

- reject unsigned tokens
- reject tokens with missing audience
- reject tokens without mapped app roles

## 2. Role-Based Access Expectations

The role matrix is defined in [security_baseline.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/security_baseline.py).

MVP roles:

- `ops_reviewer`
- `ops_supervisor`
- `compliance_reviewer`
- `fraud_reviewer`
- `ops_admin`
- `audit_reader`
- `workflow_worker`
- `integration_service`

Access expectations:

- reviewers can view cases, view documents, claim tasks, submit corrections, and escalate
- supervisors can perform reviewer actions and close cases
- compliance and fraud reviewers can close cases only within their assigned review lane
- audit readers can retrieve audit trails but cannot mutate cases
- workflow workers and integration services can use internal workflow endpoints only
- no frontend principal may call `internal/*` endpoints

Required engineering control:

- authorization must be enforced in service layer code, not only in frontend visibility
- every privileged action must log actor id, actor role, and resource identifiers

## 3. Secure File Upload Requirements

Uploads are high-risk entry points and must be tightly constrained.

Required controls:

- enforce maximum upload size from `OPS_AGENT_MAX_UPLOAD_BYTES`
- only allow MIME types from `OPS_AGENT_ALLOWED_UPLOAD_MIME_TYPES`
- verify MIME type server-side, not only from client metadata
- compute content hash on receipt
- assign server-side document ids and object keys
- store uploads in private object storage only
- quarantine files until metadata and size validation pass
- reject encrypted archives, executables, scripts, and office macros in MVP

Upload processing requirements:

- upload path must require authenticated user context
- create audit event on upload start and upload completion
- never expose raw storage keys to untrusted clients
- persist retention class with every document

MVP accepted formats:

- PDF
- PNG
- JPEG

## 4. Storage Protection Requirements

Storage must be private by default.

Required object storage controls:

- bucket is private with no anonymous read
- documents accessed only through short-lived brokered URLs or internal service fetch
- presigned URL TTL configured via `OPS_AGENT_PRESIGNED_URL_TTL_SECONDS`
- object keys must be opaque and non-guessable
- content hash stored with document metadata
- document versions are append-only

Required database controls:

- separate schemas for core, AI, review, audit, and identity data
- database credentials differ by environment
- write access for workers limited to required schemas/tables
- audit tables writable only by backend services, never by frontend directly

## 5. Encryption Requirements

Minimum encryption controls:

- TLS 1.2+ for all external and internal HTTP traffic
- TLS for database connections outside local development
- encryption at rest for Postgres volumes and object storage
- KMS-backed storage encryption key configured via `OPS_AGENT_STORAGE_KMS_KEY_ID`

Implementation requirements:

- disable plaintext transport in non-local environments
- do not log secrets, tokens, or raw document payloads
- do not store prompt/provider credentials in plaintext files

## 6. API Security Controls

Required public API controls:

- authenticate every non-health endpoint
- authorize every route by protected action
- validate request bodies with Pydantic or JSON schema
- enforce case state transition rules server-side
- attach `trace_id` to every mutating request
- rate-limit authentication failures and abusive upload attempts
- return generic error bodies for security-sensitive failures

Required response controls:

- add security headers:
  `Strict-Transport-Security`
  `X-Content-Type-Options`
  `X-Frame-Options`
  `Referrer-Policy`
  `Content-Security-Policy`
- never expose internal stack traces in API responses
- never return raw storage object keys or provider secrets

## 7. Service-To-Service Security Controls

Internal services are still security boundaries.

Required controls:

- use dedicated service identities for workflow worker and integration adapters
- validate internal token audience against `OPS_AGENT_SERVICE_AUTH_AUDIENCE`
- do not reuse browser tokens for worker calls
- restrict internal endpoints to service identities only
- pin allowed internal callers by audience and role
- include trace id and service identity in every internal call log

MVP implementation approach:

- bearer JWT with dedicated service audience
- internal network segmentation where available
- add mTLS later if the platform supports it cleanly

## 8. Secrets Handling Implementation Approach

Required secrets handling rules:

- secrets injected through environment variables or secret manager only
- `.env.example` may contain variable names and safe placeholders only
- production secrets must not exist in repo, logs, screenshots, or tests
- rotate IdP, DB, object storage, and provider credentials independently

MVP implementation approach:

- local development may use `.env` not committed to git
- deployed environments use platform secret manager or CI/CD secret store
- bootstrap scripts must fail fast when required secrets are missing

High-sensitivity secrets:

- database password
- object storage secret
- OIDC client secret if used
- provider API keys
- encryption/KMS credentials

## 9. Audit Protection Controls

Audit data is a protected system of record.

Required controls:

- audit events are append-only
- audit reads are restricted to `audit_reader`, `ops_supervisor`, and `ops_admin`
- audit writes occur only through backend services
- audit event payloads may contain evidence refs and safe summaries, not raw chain-of-thought
- audit failures must emit operational alerts
- clock source must be UTC and consistent across services

Implementation requirements:

- preserve actor id and actor role on every audit write
- preserve version refs for prompt/rule/workflow versions when relevant
- optionally add immutable hash support now; enforce hash chaining later

## 10. Secure Development Rules For Engineers

Engineers must follow these rules in code and review:

- never log raw document bodies, OCR payload dumps, or access tokens
- never bypass service-layer authorization because the frontend hides a button
- never allow direct object storage paths in browser-visible payloads
- never merge prompt or model changes without version bump and review
- never add wildcard CORS in non-local environments
- never use shared service accounts across unrelated components
- always validate uploads and response schemas server-side
- always add tests for new privileged actions and negative auth paths
- always keep internal workflow routes separate from public routes

Secure code review focus:

- authz checks present for every mutation
- no PII or token leakage in logs
- no insecure default upload behavior
- no hidden state transition shortcuts

## 11. MVP Security Baseline Checklist

Authentication and authorization:

- OIDC issuer validation wired
- audience validation wired
- role mapping implemented
- service identities separated from user identities
- internal workflow endpoints blocked from user tokens

Upload and storage:

- upload size limit enforced
- allowed MIME list enforced server-side
- file hash computed and stored
- private object storage only
- presigned URL TTL enforced

Encryption and transport:

- TLS enforced outside local
- database and object storage encrypted at rest
- KMS key configured for storage

API and service controls:

- security headers returned
- structured auth failure logging enabled
- no stack traces in API responses
- rate limiting on auth/upload endpoints
- request trace ids on all mutations

Secrets and audit:

- secrets loaded from env or secret manager only
- no secrets committed
- audit events append-only
- audit read roles restricted
- audit failure alert configured

## Acceptance Criteria

- a reviewer cannot access internal worker endpoints with a browser token
- document downloads require authenticated brokered access
- privileged actions fail closed when role claims are missing
- sensitive documents and tokens are absent from normal logs
- the required security settings are representable in config and environment bootstrap

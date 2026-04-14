# CI/CD And Environment Build Pack

This build pack defines the MVP CI/CD and environment setup for the banking Document Processing Agent (Ops Agent). It is aligned to the current repository artifacts in [.github/workflows/ci.yml](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/.github/workflows/ci.yml), [.github/workflows/deploy.yml](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/.github/workflows/deploy.yml), [.github/workflows/prompt-release.yml](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/.github/workflows/prompt-release.yml), [config.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/config.py), [.env.example](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/.env.example), and [infra/environments/README.md](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/infra/environments/README.md).

## 1. Environment Layout

The required environments are:

- `local`
- `dev`
- `staging`
- `production`

### Local

Purpose:

- developer iteration
- schema and API development
- workflow and frontend integration against stub or sandbox services

Baseline components:

- local Postgres
- local MinIO or S3-compatible object storage
- local Temporal
- local Keycloak or equivalent OIDC dev realm
- stubbed OCR and AI services by default

Restrictions:

- no real customer data
- no production secrets
- no direct access to shared regulated storage

### Dev

Purpose:

- shared integration environment for engineering teams
- contract validation across backend, frontend, workflow, and auth

Baseline components:

- managed or shared Postgres
- managed or shared object storage
- shared OIDC realm or test tenant
- workflow worker deployment
- sandbox or deterministic provider integrations

Release rule:

- branch or PR preview deployments allowed
- prompt and model changes may be validated here before staging

### Staging

Purpose:

- release-candidate validation
- migration rehearsal
- auth, audit, observability, and workflow smoke tests

Baseline components:

- production-like topology
- production-like RBAC and secrets flow
- prompt/model versions pinned exactly for release candidate testing

Release rule:

- only promoted builds from CI
- no ad hoc manual hot edits

### Production

Purpose:

- regulated banking operations

Baseline components:

- hardened OIDC integration
- private object storage
- append-only audit path
- full workflow worker deployment
- monitored API, worker, review, and audit pipelines

Release rule:

- controlled release approval required
- application and runtime-config promotions are separately governed

## 2. Config Management Approach

Configuration must be layered and typed.

Recommended layers:

1. committed defaults in code
2. committed `.env.example` for names and non-secret placeholders
3. environment-specific secret and config injection at deploy time
4. release-pinned runtime versions for prompts, rules, and models

Implementation rules:

- `AppSettings.from_env()` remains the typed runtime boundary
- secrets are not hardcoded in code or committed env files
- environment-specific values are injected by deployment platform
- application config and runtime AI config remain distinct

Config ownership split:

- application config: API, DB, object storage, auth, observability
- runtime AI config: prompt registry version, rule pack version, model release version

## 3. Secrets Handling Assumptions

Assumptions:

- secrets come from CI/CD secret store or platform secret manager
- secrets never live in committed files
- local `.env` is developer-managed and ignored by git

Required secret groups:

- database credentials
- object storage access key and secret
- OIDC client secrets where applicable
- AI provider credentials
- KMS or encryption-related credentials
- telemetry exporter credentials if needed

Rules:

- rotate secrets independently by service
- separate dev/staging/prod secrets completely
- redact secrets from logs and workflow payloads

## 4. CI Pipeline Stages

The current CI workflow is [ci.yml](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/.github/workflows/ci.yml).

MVP CI stages:

1. checkout
2. backend dependency install
3. backend tests
4. frontend dependency install
5. frontend lint
6. frontend typecheck

Recommended next CI additions:

- migration lint or migration apply against ephemeral database
- OpenAPI/schema diff validation
- authz negative tests
- artifact build stage for backend, worker, and frontend images

Blocking rule:

- no deploy workflow starts until CI is green

## 5. CD Pipeline Stages

The deployment workflow skeleton is [deploy.yml](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/.github/workflows/deploy.yml).

MVP CD stages:

1. release gate
   rerun tests and typecheck on the release target branch

2. database deployment
   apply pending migrations before app rollout

3. backend and worker rollout
   deploy backend API and workflow worker as separate units

4. frontend rollout
   deploy frontend only after backend and worker are healthy

5. post-deploy smoke validation
   health endpoint, auth smoke, queue smoke, audit write smoke

Production gate:

- manual approval before production environment job runs

## 6. Migration / Deployment Sequencing

Required order:

1. confirm CI green
2. confirm release notes and target versions
3. apply backward-compatible database migrations
4. deploy backend API
5. deploy workflow worker
6. run smoke tests
7. deploy frontend
8. enable new runtime config if the release includes prompt/rule/model changes

Rules:

- migrations must be additive before code depending on them rolls out
- worker rollout must not begin before migrations are complete
- frontend rollout must not assume unreleased backend contracts
- destructive migrations are deferred until after old code paths are drained

## 7. Model / Prompt Deployment Considerations

Model and prompt changes must be releasable without forcing a full application deploy where possible.

Separate deployment concerns:

- application deploy:
  backend image, worker image, frontend image

- runtime config deploy:
  prompt registry version,
  rule pack version,
  model release version

The dedicated runtime-config workflow is [prompt-release.yml](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/.github/workflows/prompt-release.yml).

Rules:

- prompt version changes require explicit version bump
- rule pack changes require explicit version bump
- model release changes require explicit version pin
- production runtime-config promotion must reference evaluated versions only
- rollback of prompts/models should be config-based whenever schema compatibility permits

## 8. Rollback Approach

Rollback must be explicit and controlled.

### Application rollback

Use when:

- backend, worker, or frontend deploy introduced regression

Approach:

- redeploy previous known-good image versions
- keep additive migrations in place if backward compatible
- disable newly introduced features through config if needed

### Runtime-config rollback

Use when:

- prompt quality regressed
- model behavior regressed
- rule pack created unsafe routing

Approach:

- switch prompt registry version back
- switch model release version back
- switch rule pack version back

Rules:

- do not edit released prompt versions in place
- do not roll back database schema destructively during incident response unless explicitly approved
- preserve audit trace of deployed and rolled-back versions

## 9. Required Environment Variables

The current committed baseline is in [.env.example](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/.env.example).

Required MVP variables:

- `OPS_AGENT_APP_NAME`
- `OPS_AGENT_ENV`
- `OPS_AGENT_API_VERSION`
- `OPS_AGENT_FRONTEND_BASE_URL`
- `OPS_AGENT_DATABASE_URL`
- `OPS_AGENT_OBJECT_STORE_BUCKET`
- `OPS_AGENT_OBJECT_STORE_ENDPOINT`
- `OPS_AGENT_OBJECT_STORE_REGION`
- `OPS_AGENT_OBJECT_STORE_ACCESS_KEY_ID`
- `OPS_AGENT_OBJECT_STORE_SECRET_ACCESS_KEY`
- `OPS_AGENT_TEMPORAL_NAMESPACE`
- `OPS_AGENT_TEMPORAL_HOST`
- `OPS_AGENT_KEYCLOAK_ISSUER_URL`
- `OPS_AGENT_OIDC_AUDIENCE`
- `OPS_AGENT_JWKS_CACHE_TTL_SECONDS`
- `OPS_AGENT_AUDIT_LOG_LEVEL`
- `OPS_AGENT_REVIEW_QUEUE_DEFAULT`
- `OPS_AGENT_PROMPT_REGISTRY_VERSION`
- `OPS_AGENT_RULE_PACK_VERSION`
- `OPS_AGENT_MODEL_RELEASE_VERSION`
- `OPS_AGENT_ENABLE_PROMPT_RUNTIME`
- `OPS_AGENT_MAX_UPLOAD_BYTES`
- `OPS_AGENT_ALLOWED_UPLOAD_MIME_TYPES`
- `OPS_AGENT_PRESIGNED_URL_TTL_SECONDS`
- `OPS_AGENT_STORAGE_KMS_KEY_ID`
- `OPS_AGENT_SERVICE_AUTH_AUDIENCE`
- `OPS_AGENT_OTEL_EXPORTER_OTLP_ENDPOINT`

Variable grouping:

- app/runtime
- storage
- workflow engine
- auth
- AI runtime config
- security
- observability

## 10. MVP Deployment Baseline

The MVP deployment baseline is:

- GitHub Actions for CI and controlled workflow-dispatch CD
- one backend API deploy unit
- one workflow worker deploy unit
- one frontend deploy unit
- one migration step before rollout
- runtime-config release path separated for prompt/rule/model changes
- local environment with stub providers
- dev and staging with sandbox or deterministic providers
- production with pinned prompt/model/rule versions and manual approval gate

Minimum release checks before production:

- backend tests pass
- frontend lint and typecheck pass
- migrations reviewed
- auth smoke passes
- audit smoke passes
- rollback target version identified

## Controlled Release Guidance

Application release types:

- backend-only
- frontend-only
- backend + worker
- full stack

Runtime release types:

- prompt-only
- rule-pack-only
- model-only
- combined runtime config

Preferred production sequencing:

1. promote schema
2. promote backend and worker
3. smoke test
4. promote frontend
5. promote runtime-config if included

## Acceptance Criteria

- environments are clearly separated and purpose-defined
- CI blocks broken builds from release workflows
- database rollout is sequenced ahead of app rollout
- prompt/model/rule changes can be promoted or rolled back separately from app images
- required environment variables are explicit and grouped for engineering use

# Ops Agent Monorepo Structure

This document defines the target repository layout for the banking-grade Document Processing Agent MVP.
It is optimized for:

- clear app ownership
- safe domain boundaries
- explicit workflow states
- auditable backend behavior
- simple onboarding for a multi-person team
- clean extension points for OCR and AI integrations

Current top-level implementation assets such as `src/`, `frontend/`, `contracts/`, and `openapi/` should be treated as migration-source material until the code is moved into this layout deliberately.

## Root Structure

```text
.
|-- apps/
|   |-- backend/
|   |   |-- alembic/
|   |   |   `-- versions/
|   |   |-- scripts/
|   |   |-- src/
|   |   |   `-- ops_agent/
|   |   |       |-- api/
|   |   |       |   `-- routes/
|   |   |       |-- application/
|   |   |       |   |-- services/
|   |   |       |   `-- use_cases/
|   |   |       |-- domain/
|   |   |       |   |-- audit/
|   |   |       |   |-- cases/
|   |   |       |   |-- documents/
|   |   |       |   |-- review/
|   |   |       |   |-- shared/
|   |   |       |   `-- workflow/
|   |   |       |-- infrastructure/
|   |   |       |   |-- audit/
|   |   |       |   |-- db/
|   |   |       |   |   |-- models/
|   |   |       |   |   |-- repositories/
|   |   |       |   |   `-- session/
|   |   |       |   |-- logging/
|   |   |       |   |-- observability/
|   |   |       |   |-- providers/
|   |   |       |   |-- queue/
|   |   |       |   `-- storage/
|   |   |       |-- tasks/
|   |   |       `-- workflows/
|   |   `-- tests/
|   |       |-- contract/
|   |       |-- integration/
|   |       `-- unit/
|   |-- web/
|   |   |-- public/
|   |   |-- src/
|   |   |   |-- api/
|   |   |   |-- app/
|   |   |   |-- components/
|   |   |   |-- features/
|   |   |   |-- hooks/
|   |   |   |-- lib/
|   |   |   |-- mocks/
|   |   |   |-- styles/
|   |   |   `-- types/
|   |   `-- tests/
|   |       |-- integration/
|   |       `-- unit/
|   `-- worker/
|       |-- src/
|       |   `-- ops_agent_worker/
|       |       |-- bootstrap/
|       |       `-- jobs/
|       `-- tests/
|           |-- integration/
|           `-- unit/
|-- contracts/
|-- db/
|-- docs/
|   |-- adr/
|   |-- api/
|   |-- architecture/
|   |-- operations/
|   |-- security/
|   `-- testing/
|-- infra/
|   |-- docker/
|   |-- environments/
|   |-- monitoring/
|   |-- postgres/
|   `-- redis/
|-- openapi/
|-- packages/
|   `-- contracts/
|       |-- examples/
|       |-- jsonschema/
|       `-- openapi/
|-- tests/
|   `-- e2e/
`-- tooling/
    |-- scripts/
    `-- templates/
```

## Backend Folder Structure

`apps/backend/src/ops_agent/api/`

- FastAPI routers, dependency wiring, request parsing, response shaping, and HTTP error mapping.
- No business decision logic here.

`apps/backend/src/ops_agent/application/use_cases/`

- Explicit workflow actions such as case creation, document registration, validation completion, manual decision submission, and audit retrieval.
- This is the primary home for transactional business behavior.

`apps/backend/src/ops_agent/application/services/`

- Cross-use-case orchestration and domain services that do not belong to a single HTTP endpoint.
- Good place for workflow policy coordination, file ingestion coordination, and provider dispatch services.

`apps/backend/src/ops_agent/domain/`

- Core entities, enums, value objects, workflow states, domain policies, and audit-safe status transition rules.
- Split by business concern instead of technical type to keep the model understandable.

`apps/backend/src/ops_agent/infrastructure/db/`

- SQLAlchemy models, repository implementations, session management, and database-specific adapters.
- Domain models should not depend on SQLAlchemy concerns.

`apps/backend/src/ops_agent/infrastructure/providers/`

- OCR, classification, extraction, validation, and storage adapter interfaces plus concrete provider integrations.
- Placeholder adapters should be explicitly marked and return structured results.

`apps/backend/src/ops_agent/infrastructure/queue/`

- Celery app wiring, queue routing, retry policy configuration, and job envelope helpers.

`apps/backend/src/ops_agent/tasks/`

- Task entrypoints that call application use cases or provider adapters.
- Tasks must emit explicit success, failure, and retryable outcome records.

`apps/backend/src/ops_agent/workflows/`

- Case progression orchestration and explicit step sequencing for document ingestion through decisioning and manual review.

`apps/backend/alembic/`

- Migration environment and version history.
- Keep migration logic close to the backend app, not at repository root.

`apps/backend/tests/`

- `unit/`: pure domain and application rules.
- `integration/`: database, API, and provider wiring tests.
- `contract/`: OpenAPI and schema compatibility checks.

## Frontend Folder Structure

`apps/web/src/app/`

- Vite entrypoint composition, route shells, top-level layout wiring, and page-level assembly.

`apps/web/src/features/`

- Feature slices such as `case-intake`, `review-queue`, `case-workspace`, `audit-trail`, and `manual-decision`.
- Each feature owns its tables, detail panels, API hooks, and status presentation helpers.

`apps/web/src/components/`

- Shared UI building blocks used across multiple features.
- Keep business rules out of generic components.

`apps/web/src/api/`

- API clients, request helpers, response mappers, and typed transport contracts.

`apps/web/src/lib/`

- Reusable non-UI helpers such as formatting, polling helpers, and table state utilities.

`apps/web/src/types/`

- Shared frontend-only view models and contract-derived types.

`apps/web/src/styles/`

- Tailwind entrypoints, tokens, and app-level stylesheet composition.

`apps/web/tests/`

- `unit/`: component and hook tests.
- `integration/`: feature flow and API mocking tests.

## Shared Docs and Spec Folders

`packages/contracts/`

- Canonical machine-readable artifacts.
- Prefer generating downstream clients from here instead of duplicating schemas in apps.

`docs/architecture/`

- C4-style system views, service boundaries, workflow diagrams, and modularity decisions.

`docs/api/`

- API conventions, auth model notes, pagination/error format guidelines, and example lifecycle traces.

`docs/security/`

- Data handling controls, access patterns, audit requirements, and operational guardrails.

`docs/operations/`

- Runbooks, reviewer procedures, deployment checklists, and incident handling notes.

`docs/testing/`

- Test strategy, quality gates, fixture guidance, and environment expectations.

`docs/adr/`

- Short, dated architecture decision records for key choices such as queue model, audit persistence strategy, and provider abstraction boundaries.

## Infra and Config Folders

`infra/docker/`

- Local multi-service development definitions.
- MVP should include backend, worker, postgres, and redis only.

`infra/postgres/`

- Initialization scripts, role/bootstrap notes, and dev seed helpers.

`infra/redis/`

- Local queue and cache setup assets.

`infra/monitoring/`

- Starter config for metrics, logs, tracing, and dashboards.
- Keep this lightweight for MVP.

`infra/environments/`

- Environment templates and deployment notes for `local`, `staging`, and `production`.

`tooling/`

- Repo-wide developer automation and templates that are not part of product runtime code.

## Test Folder Strategy

Use two test layers:

- app-local tests inside `apps/backend`, `apps/web`, and `apps/worker`
- system-level end-to-end tests inside `tests/e2e`

This keeps most feedback loops close to the owning code while preserving a place for true cross-runtime verification.

## Naming Conventions

- Python packages and modules: `snake_case`
- TypeScript files: `kebab-case.ts` and `kebab-case.tsx`
- React components: `PascalCase` exports, file names can remain `kebab-case.tsx`
- Database tables: plural `snake_case`
- SQLAlchemy models: singular `PascalCase`
- Pydantic request/response models: suffix with `Request`, `Response`, `Item`, or `Summary`
- Use case modules: verb-first, for example `create_case.py`, `submit_manual_decision.py`
- Task modules: outcome-oriented, for example `run_ocr_job.py`, `run_validation_job.py`
- ADR files: `YYYY-MM-DD-short-title.md`

## Module Organization Rationale

- Split runtimes by deployment unit: API, worker, and web should evolve independently.
- Keep business intent in `application` and `domain` so routes, tasks, and repositories stay replaceable.
- Separate machine-readable contracts from app code so frontend and backend can share a stable source of truth.
- Keep queue, provider, storage, and observability integrations behind infrastructure boundaries so future OCR or AI vendors do not leak into domain logic.
- Use app-local tests for fast ownership and root end-to-end tests for regulated workflow verification.
- Keep the structure MVP-first: enough room for audit logging, queueing, and provider integration without introducing unnecessary platform packages early.

## MVP Notes

- The backend and worker may share the same Python dependency lock initially, but they should remain separate runtimes.
- The web app should favor explicit review flows and evidence visibility over abstraction-heavy state management.
- AI and OCR functionality should begin as provider interfaces with placeholder adapters, not hidden inside controllers or tasks.
- Any automatic decision path must preserve manual review escape hatches and explicit audit event creation.

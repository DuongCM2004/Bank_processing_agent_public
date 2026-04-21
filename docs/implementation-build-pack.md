# Ops Agent Implementation Build Pack

This build pack is implementation-oriented and aligned to the current repository. It extends the existing FastAPI MVP with machine-readable contracts, database migrations, frontend scaffold files, workflow contracts, audit/logging helpers, and delivery structure.

## Current Documents Module Baseline

For document information extraction, implement against [production-llm-document-extraction-backend-spec.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\production-llm-document-extraction-backend-spec.md). The build target is FastAPI document upload, object storage, async workers, Pillow preprocessing, LangGraph orchestration, OpenAI GPT-4o or GPT-4o-mini Vision structured extraction, strict schema validation, one retry, normalization, manual review, approved-only PostgreSQL persistence, audit trail, and UUID search. Do not add dataset preparation, training, benchmarking, or evaluation tasks to the Documents extraction build.

## Assumptions

- Banking operations context is mandatory.
- All ambiguous, risky, or policy-gated outcomes must preserve human review.
- PostgreSQL is the transactional source of truth.
- Object storage holds raw documents and large derived artifacts.
- Temporal is the workflow engine target for production orchestration.
- The current FastAPI MVP remains the narrow public API baseline.

## 1. Recommended Tech Stack And Repo Structure

### MVP stack

- Backend API: FastAPI + Pydantic + Python 3.13
- Persistence: PostgreSQL
- Object storage: S3 or MinIO
- Workflow engine: Temporal
- Frontend: Next.js App Router + TypeScript
- Identity: Keycloak or equivalent OIDC provider
- Logging/metrics/traces: OpenTelemetry-compatible stack, Prometheus, Grafana, Loki
- Packaging/CI: GitHub Actions

### Later optimization

- Search/read model: OpenSearch
- Async broker for projections and downstream fan-out: Kafka or Redpanda
- Warehouse/analytics: ClickHouse or BigQuery
- Feature/decision model registry: MLflow or governed internal registry

### Recommended repo structure

```text
src/ops_agent/
  main.py
  service.py
  repository.py
  models.py
  config.py
  state_machine.py
  workflow_contracts.py
  prompt_registry.py
  audit_logging.py
frontend/
  package.json
  src/app/
  src/components/
  src/lib/
openapi/
  ops-agent-v1.yaml
contracts/jsonschema/
db/migrations/
docs/
tests/
.github/workflows/
```

### Engineering acceptance criteria

- Public API stays case-centric and workflow-safe.
- Frontend terminology matches backend contract names.
- DB schema supports evidence, confidence, traceability, and versioning.
- New modules do not require ripping out the current MVP before teams can start.

## 2. Backend Codebase Scaffold

### Added scaffold

- [config.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/config.py)
- [state_machine.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/state_machine.py)
- [workflow_contracts.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/workflow_contracts.py)
- [prompt_registry.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/prompt_registry.py)
- [audit_logging.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/audit_logging.py)

### MVP backend responsibilities

- `main.py`: public HTTP entrypoint
- `service.py`: workflow-safe command handling
- `repository.py`: persistence abstraction placeholder
- `state_machine.py`: explicit, testable transition policy
- `workflow_contracts.py`: internal orchestration payloads
- `audit_logging.py`: structured log event shape
- `prompt_registry.py`: bounded prompt catalog metadata

### Later optimization

- Split `repository.py` into Postgres repositories by domain schema.
- Split `service.py` into command handlers and query services.
- Add separate internal router module for Temporal signals and worker callbacks.
- Add outbox publisher and projection workers.

### Dependencies

- PostgreSQL driver and migration runner
- Temporal Python SDK
- OIDC/JWT auth middleware
- Object storage SDK

### Acceptance criteria

- State transition rules are explicit and unit-tested.
- Internal contracts are typed and version-carrying.
- Audit and prompt metadata are structurally separate from business logic.

## 3. Frontend Codebase Scaffold

### Added scaffold

- [frontend/package.json](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/frontend/package.json)
- [layout.tsx](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/frontend/src/app/layout.tsx)
- [review-queue/page.tsx](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/frontend/src/app/review-queue/page.tsx)
- [cases/[caseId]/page.tsx](</D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/frontend/src/app/cases/[caseId]/page.tsx>)
- [review-task-table.tsx](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/frontend/src/components/review-task-table.tsx)
- [field-comparison-panel.tsx](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/frontend/src/components/field-comparison-panel.tsx)
- [evidence-drawer.tsx](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/frontend/src/components/evidence-drawer.tsx)

### MVP frontend requirements

- Queue-first landing page for reviewers
- Case detail page with:
  document-linked evidence
  extracted field comparison
  validation finding display
  visible workflow status
- TypeScript types aligned to backend payloads
- No silent auto-approval UI

### Later optimization

- Split-screen document viewer with page thumbnails and bounding box overlays
- Real polling or server events
- Role-aware action permissions
- Bulk triage, workload balancing, supervisor queue views

### Acceptance criteria

- Reviewer can inspect uncertainty and evidence without leaving the case view.
- Every action path can be tied back to case id, task id, and evidence.
- UI language makes uncertainty explicit rather than smoothing it away.

## 4. Database Schema And Migration Plan

### Added migration files

- [0001_init_schemas.sql](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/db/migrations/0001_init_schemas.sql)
- [0002_core_tables.sql](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/db/migrations/0002_core_tables.sql)
- [0003_ai_rules_review_audit_tables.sql](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/db/migrations/0003_ai_rules_review_audit_tables.sql)

### MVP normalized tables

- `ops_core.cases`
- `ops_core.case_status_history`
- `ops_core.documents`
- `ops_core.document_versions`
- `ops_core.workflow_runs`
- `ops_core.workflow_step_runs`
- `ops_core.outbox_events`
- `ops_ai.artifacts`
- `ops_ai.extraction_runs`
- `ops_ai.extracted_fields`
- `ops_rules.validation_runs`
- `ops_rules.validation_results`
- `ops_rules.decision_runs`
- `ops_review.review_tasks`
- `ops_review.review_actions`
- `ops_audit.audit_events`

### Migration order

1. Create logical schemas.
2. Create operational core tables.
3. Create AI, rules, review, and audit tables.
4. Add foreign keys and indexes in the same release.
5. Seed reference packs separately: rule packs, prompt ids, queue names, retention classes.

### Later optimization

- Add partitioning for high-volume audit and workflow-step tables.
- Add legal-hold and external-reference tables.
- Add normalized evidence-ref tables where query pressure justifies them.

### Acceptance criteria

- No machine-generated critical result is stored without traceable linkage to case and document context.
- No mutable workflow action lacks an append-only audit representation.

## 5. OpenAPI Specification Draft

### Added draft

- [ops-agent-v1.yaml](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/openapi/ops-agent-v1.yaml)

### Covered public endpoints

- `GET /health`
- `POST /v1/cases`
- `GET /v1/cases/{caseId}`
- `POST /v1/cases/{caseId}/documents`
- `GET /v1/cases/{caseId}/documents/{documentId}`
- `GET /v1/cases/{caseId}/results`
- `GET /v1/review-tasks`
- `POST /v1/review-tasks/{taskId}/claim`
- `POST /v1/cases/{caseId}/field-corrections`
- `POST /v1/cases/{caseId}/escalations`
- `POST /v1/cases/{caseId}/revalidate`
- `POST /v1/cases/{caseId}/close`
- `GET /v1/cases/{caseId}/audit-events`

### Covered internal endpoints

- `POST /internal/workflows/start`
- `GET /internal/workflows/{caseId}`
- `POST /internal/workflows/{caseId}/signal-review-complete`

### Acceptance criteria

- Public contract remains stable while storage and orchestration evolve.
- Internal workflow APIs remain separate from browser-facing APIs.

## 6. Shared JSON Schemas / Contracts

### Added schemas

- [common-envelope.json](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/contracts/jsonschema/common-envelope.json)
- [case.json](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/contracts/jsonschema/case.json)
- [document-metadata.json](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/contracts/jsonschema/document-metadata.json)
- [extraction-output.json](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/contracts/jsonschema/extraction-output.json)
- [validation-output.json](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/contracts/jsonschema/validation-output.json)
- [decision-output.json](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/contracts/jsonschema/decision-output.json)
- [audit-event.json](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/contracts/jsonschema/audit-event.json)

### Contract rules

- Required versus optional fields are explicit.
- Confidence is not optional for machine outputs that influence routing.
- Evidence linkage is first-class rather than comment text.
- Versioning is carried in envelopes or version refs.

### Later optimization

- Generate Pydantic and TypeScript types from a single schema source.
- Add prompt invocation, OCR summary, and compliance evaluation schemas.

## 7. Workflow Orchestration Implementation Spec

### MVP execution path

1. `POST /v1/cases` creates case, documents, initial results, optional review task.
2. API writes operational state plus outbox event.
3. Workflow starter consumes outbox and launches Temporal workflow.
4. Workflow runs steps in order:
   intake registration
   OCR
   layout/classification
   extraction
   validation
   compliance/risk checks
   route decision
5. If route is human review, workflow pauses on review task.
6. Reviewer actions emit signal payloads back to workflow.
7. Workflow resumes, revalidates, and reaches closeable state.

### Explicit failure handling

- Retryable step failure: increment attempt count in `workflow_step_runs`
- Non-retryable failure: move case to `failed` or `review_required`
- Human-review timeout: queue supervisor alert, do not auto-close
- Downstream dependency outage: retain case state, emit audit event, surface retryable status

### Later optimization

- Per-step retry policy tuning
- Dead-letter queue and replay tooling
- Supervisor intervention signals

### Acceptance criteria

- Workflow progress is externally visible through durable state.
- No step bypasses the case state machine.
- Human review is a pause-and-resume workflow gate, not a side note.

## 8. Agent Execution And Prompt Integration Spec

### MVP prompt stance

- Rules first
- ML second
- LLM only for bounded ambiguity resolution or reviewer assist

### Added supporting artifact

- [prompt_registry.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/prompt_registry.py)

### Allowed prompt-driven tasks in MVP

- OCR span reconciliation
- Document classification tiebreak
- Field extraction reconciliation
- Compliance summary for humans
- Review copilot summary

### Required stored metadata for every prompt invocation

- prompt id
- prompt version
- model id and model version
- input artifact ids
- output artifact id
- trace id
- case id and document id where applicable
- token and latency metrics

### Hard rules

- No autonomous approval or rejection
- No autonomous compliance clearance
- No hidden use of prompt outputs without audit trail
- If evidence is insufficient, status must remain review-oriented

### Acceptance criteria

- Every material prompt output is replayable and attributable.
- Prompt outputs map to versioned schemas and bounded roles.

## 9. Audit Logging And Observability Implementation Spec

### Added supporting artifact

- [audit_logging.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/audit_logging.py)

### Required log dimensions

- `trace_id`
- `case_id`
- `document_id`
- `review_task_id`
- `workflow_run_id`
- `event_name`
- `severity`

### Required audit event coverage

- case creation
- document registration
- state transitions
- workflow start and completion
- review task creation and claim
- manual corrections
- escalations
- revalidation
- close actions
- workflow failures and retries

### Minimum metrics

- case intake latency
- workflow step latency by step
- OCR/extraction/validation failure counts
- review queue age
- claim-to-close duration
- prompt invocation count, error rate, cost, and latency

### Later optimization

- distributed tracing end-to-end
- immutable hash chain for audit events
- regulator export bundle tooling

## 10. Security Baseline Implementation Spec

### MVP controls

- OIDC bearer auth for all protected APIs
- role-based authorization at service layer
- document object access only through brokered signed URLs or internal service path
- encryption in transit and at rest
- request and audit trace ids on all mutations
- immutable audit event write path
- no direct browser access to internal workflow endpoints
- secret injection via environment or secret manager only

### Data handling controls

- PII field masking in logs
- prompt inputs limited to minimum necessary evidence
- raw documents never embedded in free-form logs
- retention class stored with every document

### Later optimization

- row-level security or scoped data access
- hardware-backed key management
- legal hold and evidence-preservation controls
- signed audit export manifests

### Acceptance criteria

- Unauthorized users cannot claim, close, or escalate cases outside their role.
- Sensitive document content is not exposed through logs or generic API responses.

## 11. Testing Scaffold And Test Plan For Engineering

### Added tests

- [test_api.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/tests/test_api.py)
- [test_state_machine.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/tests/test_state_machine.py)
- [test_build_pack_assets.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/tests/test_build_pack_assets.py)

### MVP test layers

- Unit:
  state machine rules
  service command guards
  audit event creation
  prompt registry validation
- Contract:
  OpenAPI presence
  JSON schema parse validity
  request/response payload tests
- API integration:
  create, claim, correct, revalidate, close
  invalid transition rejection
  closed-case document rejection
- DB migration:
  apply schema from clean database
- Frontend:
  typecheck
  component rendering for evidence and validation states

### Later optimization

- Temporal workflow integration tests
- object storage integration tests
- authz matrix tests by role
- prompt regression/evaluation suite
- load tests on queue operations and audit retrieval

## 12. CI/CD And Environment Structure

### Added artifacts

- [ci.yml](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/.github/workflows/ci.yml)
- [.env.example](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/.env.example)

### MVP environments

- `local`
- `dev`
- `staging`
- `prod`

### Deployment expectations

- Backend and worker deployments are separate units.
- Frontend deploys separately but shares versioned API contract.
- DB migration job runs before backend promotion.
- Prompt registry and rule-pack versions are pinned per release.

### Acceptance criteria

- Backend CI runs tests on every PR.
- Frontend scaffold typechecks in CI.
- Environment contract is explicit and versionable.

## 13. Developer Task Breakdown By Sprint / Workstream

### Sprint 1: Foundation

1. Backend workstream
   Dependency: none
   Deliverables: Postgres repository implementation, migration runner, auth middleware skeleton
   Acceptance criteria: app boots against Postgres, auth context is injectable, migrations apply cleanly
2. Workflow workstream
   Dependency: migration baseline
   Deliverables: Temporal workflow skeleton, outbox consumer, workflow status persistence
   Acceptance criteria: case creation launches a persisted workflow run
3. Frontend workstream
   Dependency: OpenAPI draft
   Deliverables: review queue, case detail shell, API client wiring
   Acceptance criteria: reviewer can load queue and case detail from API
4. Platform/security workstream
   Dependency: env structure
   Deliverables: secret handling, OIDC setup, access policy matrix
   Acceptance criteria: protected endpoints reject unauthenticated requests

### Sprint 2: Processing and review loop

1. AI ingestion/extraction workstream
   Dependency: workflow skeleton, artifact registry tables
   Deliverables: OCR adapter, extraction adapter, result persistence
   Acceptance criteria: document processing creates persisted extraction and validation records
2. Review operations workstream
   Dependency: frontend shell, backend review APIs
   Deliverables: claim, correction, escalation, revalidation, close flows wired end to end
   Acceptance criteria: reviewer actions update workflow state and audit history
3. Observability workstream
   Dependency: workflow and API tracing keys
   Deliverables: structured logs, metrics, dashboard baseline
   Acceptance criteria: team can trace one case across API, workflow, and review action logs

### Sprint 3: Controls hardening

1. Compliance/risk workstream
   Dependency: extraction and validation persistence
   Deliverables: compliance control evaluation service, specialist queue routing
   Acceptance criteria: pending critical checks always force review or escalation
2. Quality engineering workstream
   Dependency: stable contracts
   Deliverables: contract, integration, authz, and workflow replay tests
   Acceptance criteria: critical workflow regressions are caught before merge
3. Release engineering workstream
   Dependency: CI foundation
   Deliverables: staging promotion pipeline and rollback runbook
   Acceptance criteria: release can be promoted and rolled back without manual DB drift

## Consistency Check

- Public API endpoints in the build pack match the current FastAPI MVP behavior.
- State transitions in the documentation align with [state_machine.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/state_machine.py) and the live service.
- Migration tables cover the entities referenced by the OpenAPI and JSON schema artifacts.
- Frontend scaffold uses the same case, review task, field, validation, and evidence concepts as the backend.
- Prompt integration spec stays advisory and bounded; it does not authorize unsafe autonomous decisions.

## Implementation Blockers

- No Postgres repository implementation yet; current runtime is still in-memory only.
- No Temporal worker or outbox processor exists yet.
- No auth middleware or authorization checks are wired into the running API.
- No object storage adapter or artifact broker exists yet.
- Frontend scaffold is static until API integration and runtime config are completed.
- OpenAPI and JSON schemas are draft artifacts and not yet generated from a single source of truth.

## Recommended Next Build Steps

1. Replace `InMemoryRepository` with a Postgres-backed repository layer while keeping API signatures stable.
2. Add migration execution and local Docker Compose for Postgres, MinIO, Temporal, and Keycloak.
3. Wire OIDC auth and role checks into review and close endpoints first.
4. Implement workflow start/outbox persistence and a Temporal starter worker.
5. Connect the frontend queue and case pages to live API calls behind auth.
6. Add artifact registry writes and document-version persistence before integrating OCR or LLM components.

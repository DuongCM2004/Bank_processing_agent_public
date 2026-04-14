# Engineering Execution Plan

This plan breaks the Ops Agent build into assignable engineering tasks. It is aligned to the current repository scaffold and the implementation specs already added in `docs/`.

## Planning Assumptions

- Sprint length: 2 weeks
- MVP target: conservative, review-first banking operations flow
- Team model: small cross-functional squad with backend, frontend, platform, QA, and security coverage
- Sequence principle: unblock the regulated control path first, optimize later

## 1. Workstreams By Team / Role

### Backend Platform

Scope:

- Postgres persistence
- API wiring
- state-safe service logic
- artifact metadata persistence

Suggested owners:

- 1 senior backend engineer
- 1 backend engineer

### Workflow / Integration

Scope:

- Temporal workflow starter and worker
- outbox processor
- provider adapter wiring
- internal workflow contracts

Suggested owners:

- 1 backend engineer
- 1 platform/integration engineer

### Frontend Ops Dashboard

Scope:

- review queue
- case workspace
- document/evidence comparison
- auth-aware API integration

Suggested owners:

- 1 senior frontend engineer
- 1 frontend engineer

### Security / IAM

Scope:

- OIDC auth
- role enforcement
- upload controls
- internal service auth

Suggested owners:

- 1 security engineer
- support from backend lead

### QA / Release Quality

Scope:

- test harness
- integration suites
- release quality gates
- regression ownership

Suggested owners:

- 1 QA engineer
- support from engineering lead

### DevOps / MLOps / Observability

Scope:

- CI/CD
- environment wiring
- metrics/logging/dashboards
- prompt/model promotion flow

Suggested owners:

- 1 DevOps engineer
- support from observability-minded backend engineer

## 2. Sprint-By-Sprint Task Breakdown

## Sprint 1: Foundation And Control Plane

### BE-01: Implement Postgres repository for cases/documents/review/audit

Owner:

- Backend Platform

Dependencies:

- existing migration files

Can run in parallel with:

- FE-01, SEC-01, DEVOPS-01

Acceptance criteria:

- repository layer persists cases, documents, review tasks, review actions, and audit events
- current API tests can be adapted to run against Postgres-backed repository
- no state behavior regression versus current in-memory implementation

### BE-02: Add migration runner and database bootstrap command

Owner:

- Backend Platform

Dependencies:

- BE-01 not required

Can run in parallel with:

- BE-01

Acceptance criteria:

- clean database can apply all migrations in order
- migration execution is callable in CI/CD
- failed migration returns non-zero exit and clear operator output

### WF-01: Implement workflow run persistence and outbox publish path

Owner:

- Workflow / Integration

Dependencies:

- BE-01

Acceptance criteria:

- case creation persists workflow start intent durably
- outbox rows contain typed workflow start payload
- duplicate start requests are idempotent

### WF-02: Implement Temporal starter workflow skeleton

Owner:

- Workflow / Integration

Dependencies:

- WF-01

Acceptance criteria:

- workflow run can start from persisted start command
- workflow status is queryable
- workflow step ordering matches existing workflow policy

### SEC-01: Wire OIDC token validation middleware

Owner:

- Security / IAM

Dependencies:

- config and environment baseline already present

Can run in parallel with:

- BE-01, FE-01

Acceptance criteria:

- protected endpoints reject missing or invalid bearer tokens
- issuer and audience are validated
- user identity and roles are available to service layer

### SEC-02: Enforce role-based access on review and close actions

Owner:

- Security / IAM

Dependencies:

- SEC-01

Acceptance criteria:

- claim, correction, escalation, close, audit-read routes enforce role matrix
- unauthorized actions fail closed
- negative auth tests exist for privileged routes

### FE-01: Wire frontend API client to live authenticated backend

Owner:

- Frontend Ops Dashboard

Dependencies:

- SEC-01
- stable case/review API routes

Acceptance criteria:

- queue page loads from live API
- case page loads live case details
- auth failures are rendered safely

### DEVOPS-01: Add local environment bootstrap for Postgres/MinIO/Temporal/Keycloak

Owner:

- DevOps / MLOps

Dependencies:

- none

Acceptance criteria:

- developer can start required local services with one documented command path
- environment variables are documented and consumable
- local bootstrap does not require production secrets

### QA-01: Restructure tests into unit/integration scaffolding without breaking current suite

Owner:

- QA / Release Quality

Dependencies:

- none

Can run in parallel with all Sprint 1 tasks

Acceptance criteria:

- new tests can be added under unit/integration folders
- shared fixtures and stubs are reusable
- existing test suite still passes

## Sprint 2: Processing Loop And Review Operations

### INT-01: Implement object storage adapter and document version persistence

Owner:

- Backend Platform

Dependencies:

- BE-01
- DEVOPS-01

Acceptance criteria:

- uploads persist metadata and object references
- document versions are append-only
- raw storage keys are not exposed to clients

### SEC-03: Enforce secure upload validation path

Owner:

- Security / IAM

Dependencies:

- INT-01

Acceptance criteria:

- upload size limit enforced
- MIME allowlist enforced server-side
- file hash recorded
- failed uploads generate audit and operational logs

### WF-03: Implement OCR and parsing activity boundaries with stub providers

Owner:

- Workflow / Integration

Dependencies:

- WF-02
- INT-01

Acceptance criteria:

- workflow executes OCR and parsing steps independently
- retry and timeout behavior follows workflow policy
- step results and artifacts are persisted

### AI-01: Implement classification and extraction adapters with schema-bound outputs

Owner:

- Workflow / Integration

Dependencies:

- WF-03
- agent runtime scaffold

Acceptance criteria:

- classification and extraction outputs validate against declared schemas
- low-confidence outputs route to review
- schema-invalid outputs fail safely

### AI-02: Implement validation and decision routing services

Owner:

- Backend Platform

Dependencies:

- AI-01

Acceptance criteria:

- validation findings persist with evidence refs
- decision routing never auto-closes a case
- review-required routing is explicit and auditable

### FE-02: Implement manual review actions end to end

Owner:

- Frontend Ops Dashboard

Dependencies:

- FE-01
- SEC-02
- AI-02

Acceptance criteria:

- reviewer can claim task, correct field, escalate, and request revalidation
- UI shows evidence-linked comparison
- actions refresh case state and audit history

### OBS-01: Implement structured operational logging and audit write hooks

Owner:

- DevOps / MLOps
- Backend support

Dependencies:

- WF-02
- AI-01

Acceptance criteria:

- workflow steps emit operational logs at boundaries
- audit events are written on required case/review mutations
- trace ids correlate API, workflow, and review actions

### QA-02: Add integration tests for auth, upload, review loop, and low-confidence routing

Owner:

- QA / Release Quality

Dependencies:

- SEC-02
- SEC-03
- FE-02
- AI-02

Acceptance criteria:

- integration suite covers unauthorized action rejection
- upload validation failures covered
- low-confidence scenario covered
- correction -> revalidation flow covered

## Sprint 3: Hardening And Release Readiness

### RISK-01: Implement compliance and fraud specialist routing

Owner:

- Backend Platform
- Workflow / Integration support

Dependencies:

- AI-02

Acceptance criteria:

- sanctions/AML/fraud reason codes route to specialist queues
- specialist review actions remain role-gated
- specialist queue behavior is observable

### OBS-02: Implement MVP dashboards and alert thresholds

Owner:

- DevOps / MLOps

Dependencies:

- OBS-01

Acceptance criteria:

- operations queue dashboard exists
- workflow health dashboard exists
- audit pipeline dashboard exists
- alerts fire for queue age, audit write failure, workflow failure spike

### DEVOPS-02: Wire deploy workflow, migration sequencing, and runtime-config promotion

Owner:

- DevOps / MLOps

Dependencies:

- BE-02
- WF-02

Acceptance criteria:

- deploy workflow applies migrations before rollout
- backend, worker, and frontend are separable deploy units
- prompt/model/rule promotion can run independently

### QA-03: Add release-candidate e2e workflow suite

Owner:

- QA / Release Quality

Dependencies:

- FE-02
- RISK-01
- DEVOPS-02

Acceptance criteria:

- happy path, low-confidence path, escalation path, and retry exhaustion path all execute in staging
- audit trail assertions included in release candidate run

### SEC-04: Final MVP hardening review

Owner:

- Security / IAM

Dependencies:

- SEC-03
- DEVOPS-02
- OBS-02

Acceptance criteria:

- internal endpoints blocked from user tokens
- upload and storage protections verified
- secrets handling and audit read restrictions verified

## 3. Task Ownership Suggestions

Recommended ownership mapping:

| Task | Primary owner | Secondary reviewer |
|---|---|---|
| BE-01 | Senior backend engineer | Engineering lead |
| BE-02 | Backend engineer | DevOps engineer |
| WF-01 | Backend engineer | Senior backend engineer |
| WF-02 | Platform/integration engineer | Backend lead |
| SEC-01 | Security engineer | Backend lead |
| SEC-02 | Security engineer | QA engineer |
| FE-01 | Senior frontend engineer | Backend lead |
| DEVOPS-01 | DevOps engineer | Security engineer |
| QA-01 | QA engineer | Engineering lead |
| INT-01 | Backend engineer | Security engineer |
| SEC-03 | Security engineer | Backend engineer |
| WF-03 | Platform/integration engineer | QA engineer |
| AI-01 | Platform/integration engineer | Backend lead |
| AI-02 | Senior backend engineer | Risk/compliance stakeholder |
| FE-02 | Frontend engineer | QA engineer |
| OBS-01 | DevOps engineer | Backend engineer |
| QA-02 | QA engineer | Engineering lead |
| RISK-01 | Senior backend engineer | Compliance reviewer |
| OBS-02 | DevOps engineer | Ops lead |
| DEVOPS-02 | DevOps engineer | Engineering manager |
| QA-03 | QA engineer | Engineering lead |
| SEC-04 | Security engineer | Engineering manager |

## 4. Dependencies Between Tasks

Parallelizable tasks in Sprint 1:

- BE-01, BE-02, SEC-01, DEVOPS-01, QA-01

Serial dependencies:

- WF-01 depends on BE-01
- WF-02 depends on WF-01
- SEC-02 depends on SEC-01
- FE-01 depends on SEC-01 and stable API responses
- INT-01 depends on BE-01 and DEVOPS-01
- AI-01 depends on WF-03
- AI-02 depends on AI-01
- FE-02 depends on AI-02 and SEC-02
- QA-02 depends on FE-02 and security/upload controls
- RISK-01 depends on AI-02
- DEVOPS-02 depends on migration and workflow rollout maturity
- QA-03 depends on FE-02, RISK-01, DEVOPS-02
- SEC-04 depends on final deploy and observability wiring

## 5. Acceptance Criteria Per Task

Acceptance criteria are embedded with each task above and must be treated as release-blocking completion criteria, not optional notes.

Task completion rule:

- code merged
- tests added or updated
- relevant documentation updated
- feature is observable and auditable if it affects workflow or security

## 6. Blockers And Prerequisite Tasks

Current blockers:

- Postgres repository is not implemented yet
- object storage adapter is not implemented yet
- auth middleware is not wired into live API
- Temporal worker does not exist yet
- frontend is scaffolded but not live-wired

Prerequisite tasks before processing-loop delivery:

- BE-01
- WF-01
- SEC-01
- DEVOPS-01

Prerequisite tasks before production-like staging:

- SEC-02
- SEC-03
- OBS-01
- DEVOPS-02
- QA-02

## 7. MVP Critical Path

Critical path tasks:

1. BE-01
2. WF-01
3. WF-02
4. SEC-01
5. SEC-02
6. INT-01
7. WF-03
8. AI-01
9. AI-02
10. FE-02
11. QA-02
12. DEVOPS-02
13. QA-03
14. SEC-04

Reason:

- this path establishes durable persistence, secure auth, executable workflow, human review loop, and release safety

## 8. Test And Integration Tasks

Required test tasks by owner:

### QA-T01: Add repository and migration integration tests

Owner:

- QA engineer

Dependencies:

- BE-01, BE-02

Acceptance criteria:

- migrations apply on clean DB
- repository CRUD and audit persistence covered

### QA-T02: Add authz negative test matrix

Owner:

- QA engineer

Dependencies:

- SEC-02

Acceptance criteria:

- reviewers, supervisors, audit readers, and service identities are tested against allowed and denied routes

### QA-T03: Add provider stub-based workflow tests

Owner:

- QA engineer

Dependencies:

- WF-03, AI-01, AI-02

Acceptance criteria:

- retryable failure and non-retryable failure paths covered
- low-confidence routing assertions covered

### QA-T04: Add staging smoke and release-candidate checklist automation

Owner:

- QA engineer
- DevOps support

Dependencies:

- DEVOPS-02

Acceptance criteria:

- deployment validation covers health, auth, queue, workflow start, review action, and audit write smoke tests

## 9. Hardening Tasks Before Release

Release hardening tasks:

### HARD-01: Audit protection verification

Owner:

- Security engineer

Acceptance criteria:

- audit read restrictions verified
- append-only path verified
- audit failure alert tested

### HARD-02: Queue backlog and timeout tuning

Owner:

- Workflow / Integration
- Ops input

Acceptance criteria:

- retry/timeout settings reviewed against staging behavior
- aged-task alert thresholds defined

### HARD-03: Prompt/runtime release guardrails

Owner:

- DevOps / MLOps
- Backend lead

Acceptance criteria:

- prompt/model/rule versions are pinned per release
- rollback procedure tested in staging

### HARD-04: Secure upload abuse checks

Owner:

- Security engineer
- QA engineer

Acceptance criteria:

- oversize, invalid MIME, duplicate, and malformed upload cases are tested

### HARD-05: Ops runbook and rollback rehearsal

Owner:

- Engineering manager
- DevOps engineer

Acceptance criteria:

- release checklist published
- rollback path rehearsed in staging
- task ownership for incident response assigned

## Parallel Work Guidance

Tasks that should run in parallel:

- backend persistence and migration work
- auth middleware and local environment setup
- frontend API integration after auth contract stabilizes
- observability instrumentation while provider adapters are being implemented
- QA scaffold work from Sprint 1 onward

Tasks that should not run prematurely:

- e2e workflow automation before workflow worker exists
- production release automation before migration and rollback sequencing is stable
- specialist risk routing before generic validation and review loop work

## Execution Summary

The first sprint should finish with:

- Postgres-backed persistence
- migration runner
- OIDC validation
- workflow start persistence
- local environment bootstrap

The second sprint should finish with:

- working processing loop through review
- secure uploads
- evidence-linked reviewer actions
- integration tests around failure and low-confidence behavior

The third sprint should finish with:

- specialist routing
- dashboards and alerts
- controlled deployment and rollback
- release-candidate test suite
- final security signoff

## Acceptance Criteria

- every task is small enough to assign to a single owner for a sprint
- dependencies and blockers are explicit
- the human-review banking-safe path is the core of the critical path
- tasks that can run in parallel are separated from those that cannot

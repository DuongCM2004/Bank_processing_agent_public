# Backend Engineering Blueprint for Ops Agent

## Role

Backend Engineer for a banking-grade Document Processing Agent.

## Objective

Build the backend services, workflow orchestration, APIs, persistence, and service integrations required to run the document processing platform safely and reliably.

## Current Extraction Baseline

The backend implementation target for the Documents module is [production-llm-document-extraction-backend-spec.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\production-llm-document-extraction-backend-spec.md).

Backend teams must treat document information extraction as an inference-only workflow:

1. FastAPI accepts image/PDF upload and returns `document_uuid`, `extraction_uuid`, and `queued` status.
2. Object storage stores raw files, preprocessed page images, raw LLM responses, and normalized payload artifacts.
3. Async workers run Python/Pillow preprocessing and base64 data URL encoding.
4. LangGraph owns the extraction graph and retry routing.
5. OpenAI GPT-4o or GPT-4o-mini Vision performs structured JSON extraction.
6. Pydantic or JSON Schema enforces the identity-document schema with no additional fields.
7. Validation failure triggers one retry with a stricter prompt.
8. Normalized JSON becomes an editable review table.
9. Review approval is required before production persistence.
10. Audit events and UUID search are mandatory for every lifecycle step.

Do not design backend extraction as dataset preparation, model training, model testing, benchmarking, evaluation, or traditional OCR engine integration.

## Assumptions

1. The current repo already contains an MVP FastAPI foundation with case creation, document registration, review tasks, corrections, escalations, revalidation, closure, and audit event retrieval.
2. Future architecture must preserve the current case-state model while moving from in-memory persistence to production-grade services and durable storage.
3. Backend orchestration must remain explicit, observable, and replayable.
4. No high-risk failure may be hidden behind silent retries or implicit fallbacks.
5. Backend services must expose enough metadata for compliance, audit, and human review.

## Deliverables

- Backend architecture
- APIs
- Workflow design
- Queue strategy
- Persistence
- State machine
- Error handling

## Dependencies

1. [solution-architecture-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\solution-architecture-blueprint.md)
2. [ai-architecture.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ai-architecture.md)
3. [data-engineering-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\data-engineering-blueprint.md)
4. [compliance-risk-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\compliance-risk-controls.md)
5. [banking-document-rules.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\banking-document-rules.md)

## Risks

1. hidden coupling between synchronous APIs and async workflow execution
2. ambiguous state transitions across services
3. retries causing duplicate processing or duplicate audit events
4. search indexes becoming mistaken for source of truth
5. backend services leaking privileged data or allowing unauthorized actions

## MVP vs Scale notes

### MVP

1. keep service count logical but operationally manageable
2. prefer one repository with modular services over fragmented independent repos
3. use LangGraph for extraction orchestration and Celery, Redis Queue, or background workers for compute dispatch
4. keep API contracts stable and narrow

### Scale

1. split services further only when ownership, throughput, or release cadence requires it
2. add HA, failover, and regional partitioning after workflow semantics are stable
3. externalize more configuration and policy controls once service boundaries mature

## 1. Backend Architecture

## 1.1 Service map

| Service | Responsibility | Runtime |
|---|---|---|
| `api-gateway` | ingress, auth forwarding, rate limiting, routing | Kong or Nginx |
| `document-upload-service` | document intake, checksum, storage registration, UUID creation | FastAPI |
| `document-status-service` | document and extraction status APIs | FastAPI |
| `workflow-service` | async extraction job dispatch and workflow-visible status API | FastAPI |
| `manual-review-service` | editable table review, approval, rejection, reviewed payload validation | FastAPI |
| `audit-service` | immutable event write and event query | FastAPI |
| `preprocessing/extraction/validation/retry workers` | Pillow preprocessing, GPT-4o Vision calls, schema validation, retry, normalization | Celery or background workers |

## 1.2 Service boundary rule

Each backend service owns:

1. its API layer,
2. its domain logic,
3. its database writes for owned entities,
4. its emitted events,
5. its audit side effects.

No service may mutate another service's private persistence tables directly.

## 1.3 Backend runtime pattern

1. API services remain stateless.
2. PostgreSQL stores durable state.
3. S3 / MinIO stores source and derived artifacts.
4. Event or queue infrastructure distributes extraction jobs and audit-worthy lifecycle events.
5. LangGraph manages extraction node execution and one retry.
6. Celery, Redis Queue, or background workers execute async preprocessing, extraction, validation, and normalization tasks.

## 2. API Specification

## 2.1 External API groups

### Documents APIs

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/documents/upload` | upload document, store raw file, create document and extraction UUIDs, queue extraction |
| `GET` | `/documents/{uuid}/status` | fetch document and latest extraction status |
| `GET` | `/documents/{uuid}/extraction` | fetch extracted and reviewed data for editable table UI |
| `POST` | `/documents/{uuid}/review` | submit reviewer edit, approval, or rejection |
| `GET` | `/audit/{uuid}` | fetch audit events by document or extraction UUID |

### Review APIs

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/v1/review-tasks` | list review tasks by queue/status |
| `POST` | `/v1/review-tasks/{task_id}/claim` | claim a task |
| `POST` | `/v1/cases/{case_id}/field-corrections` | submit reviewer corrections |
| `POST` | `/v1/cases/{case_id}/escalations` | escalate case to specialist queue |
| `POST` | `/v1/cases/{case_id}/revalidate` | rerun downstream validation after correction |
| `POST` | `/v1/cases/{case_id}/close` | close case with approved/rejected/closed_without_decision |

### System APIs

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | health probe |
| `GET` | `/ready` | readiness probe for dependencies |
| `GET` | `/metrics` | Prometheus metrics endpoint |

## 2.2 Internal APIs

### Workflow service

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/internal/documents/{document_uuid}/extract` | start queued extraction run |
| `GET` | `/internal/extractions/{extraction_uuid}/status` | inspect extraction run status |
| `POST` | `/internal/extractions/{extraction_uuid}/complete-review` | finalize approved or rejected review action |

### AI / rules services

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/internal/preprocessing/jobs` | submit image preprocessing task |
| `POST` | `/internal/extraction/jobs` | submit extraction task |
| `POST` | `/internal/validation/jobs` | submit validation task |
| `POST` | `/internal/normalization/jobs` | submit normalization task |

## 2.3 API contract principles

1. Every request and response must include or derive a `trace_id`.
2. APIs must return explicit `error_code`, `message`, `trace_id`, and `retryable` on failure.
3. Mutating APIs must be idempotent where practical via client request IDs or workflow-controlled dedupe.
4. APIs must not expose internal stack traces to clients.

## 2.4 Error response contract

```json
{
  "error_code": "case_not_found",
  "message": "Case case_123 was not found.",
  "trace_id": "uuid",
  "retryable": false,
  "details": {
    "case_id": "case_123"
  }
}
```

## 3. Workflow Orchestration Design

## 3.1 Why LangGraph

LangGraph is the correct extraction orchestration layer because the backend requires:

1. durable state across restarts,
2. explicit extraction nodes,
3. conditional retry routing,
4. validation-aware branching,
5. replayable extraction run metadata.

## 3.2 Workflow model

One extraction graph per `extraction_uuid`:

1. preprocess document image or PDF page,
2. call GPT-4o Vision or GPT-4o-mini with strict JSON schema,
3. validate output,
4. retry once if schema validation fails,
5. normalize valid JSON into editable table rows,
6. finalize as `extracted`, `in_review`, or `failed`.

## 3.3 Orchestration semantics

1. LangGraph owns extraction node execution and retry routing.
2. PostgreSQL owns domain state.
3. Workflow transitions only after successful durable writes.
4. Every transition emits an audit event.
5. Human review completion is modeled as an explicit review command, not a polling side effect.

## 4. Queue / Job Design

## 4.1 Queue separation

| Queue / topic | Purpose | Worker type |
|---|---|---|
| `document.uploaded` | new document upload event | queue consumer |
| `preprocessing.jobs` | image validation, PDF rendering, resize, base64 encoding | Celery or background worker |
| `extraction.jobs` | GPT-4o Vision structured extraction | Celery or background worker |
| `validation.jobs` | validation tasks | Celery worker |
| `normalization.jobs` | flatten strict JSON into table rows | Celery or background worker |
| `review.required` | review task creation event | queue consumer |
| `pipeline.dlq` | dead-letter failures | DLQ handler |

## 4.2 Job contract

Every job payload must include:

1. `trace_id`
2. `case_id`
3. `document_id` if applicable
4. `workflow_run_id`
5. `attempt_no`
6. `producer_service`
7. `artifact_refs`
8. `version_refs`

## 4.3 Idempotency strategy

1. Use deterministic job IDs derived from `case_id`, `document_id`, `step_name`, and `version`.
2. Persist job execution records with status `queued`, `running`, `completed`, `failed`.
3. Ignore duplicate completions if a durable successful result already exists for the same step/version.

## 4.4 Outbox pattern

Use a PostgreSQL outbox table for all externally published events:

1. write domain change and outbox record in same transaction
2. outbox publisher emits to Kafka
3. mark outbox record published

This prevents state/event divergence.

## 5. Persistence Design

## 5.1 Source-of-truth rules

1. PostgreSQL is the system of record for metadata and workflow state.
2. S3 / MinIO is the system of record for raw files and derived evidence artifacts.
3. OpenSearch is a projection only.

## 5.2 Persistence behavior by domain

### Cases and workflow state

- durable write to PostgreSQL before workflow progression
- explicit `updated_at_utc`
- optimistic locking or version column for concurrent review actions

### Documents

- immutable raw object key per version
- no overwrite of source evidence
- store content hash and storage metadata

### AI artifacts

- write artifact to S3 first
- persist artifact registry row second
- then emit completion event

### Audit

- append-only
- no hard-delete in production
- immutable storage copy for regulated retention

## 5.3 Transaction rules

1. External side effects should follow durable DB writes when possible.
2. If external side effect happens first, record compensating failure state explicitly.
3. Never mark workflow step complete before persistence succeeds.

## 6. Case State Machine

## 6.1 Primary states

Reuse and preserve the current explicit state model:

1. `received`
2. `stored`
3. `queued`
4. `processing`
5. `validated`
6. `review_required`
7. `in_review`
8. `corrected`
9. `approved`
10. `rejected`
11. `escalated`
12. `failed`
13. `closed`

## 6.2 Transition rules

| From | To | Trigger |
|---|---|---|
| `received` | `stored` | document registration persisted |
| `stored` | `queued` | workflow accepted for processing |
| `queued` | `processing` | child workflows started |
| `queued` | `review_required` | early review gate or intake exception |
| `processing` | `validated` | validations completed successfully |
| `processing` | `failed` | unrecoverable processing failure |
| `processing` | `review_required` | low confidence or validation issue |
| `validated` | `review_required` | compliance or policy gate requires review |
| `validated` | `approved` | allowed low-risk route plus approval gate satisfied |
| `validated` | `rejected` | human rejection or rule-based hard fail confirmed |
| `review_required` | `in_review` | reviewer claims task |
| `in_review` | `corrected` | reviewer submits corrections |
| `in_review` | `escalated` | reviewer escalates |
| `in_review` | `approved` | authorized reviewer approves |
| `in_review` | `rejected` | authorized reviewer rejects |
| `corrected` | `validated` | revalidation completes |
| `corrected` | `review_required` | corrections still unresolved |
| `escalated` | `in_review` | specialist resumes review |
| `escalated` | `closed` | authorized closure after escalation path |
| `approved` | `closed` | close action |
| `rejected` | `closed` | close action |
| `failed` | `review_required` | manual recovery path |
| `failed` | `closed` | explicit operational closeout |

## 6.3 Compliance state handling

Operational case state and compliance control state must remain separate.

1. A case may be `validated` while compliance is still `partial_compliance`.
2. A case must not be auto-closed while critical compliance checks are pending.
3. Compliance service writes control statuses independently of operational workflow state.

## 7. Error Handling and Retry Strategy

## 7.1 Error classes

| Error class | Example | Retryable |
|---|---|---|
| client validation error | bad request schema | no |
| domain conflict | invalid state transition | no |
| missing dependency | artifact ref missing | usually no until repaired |
| transient infra error | DB timeout, broker timeout | yes |
| worker capacity issue | GPU saturation | yes |
| external dependency pending | sanctions adapter unavailable | partial, route as pending |
| unrecoverable document error | corrupted file | no, manual path |

## 7.2 Retry policy

1. synchronous API writes:
   - no blind retries on client side
   - return explicit retryable flags
2. worker tasks:
   - exponential backoff with jitter
   - max attempts per step
3. OCR:
   - GPU retry twice
   - CPU fallback once
4. compliance adapters:
   - bounded retries
   - then mark check `pending`
5. publish failures:
   - use outbox retry loop

## 7.3 Failure visibility

Backend must never hide failures by silently swallowing them.

On every important failure:

1. write audit event
2. update case or step status
3. emit failure metric
4. send to DLQ or manual queue where relevant

## 7.4 Dead-letter strategy

1. Any async step exceeding max retries publishes to `pipeline.dlq`.
2. DLQ records include `case_id`, `document_id`, `step_name`, `error_code`, `trace_id`, `version_refs`.
3. DLQ creates a visible operations incident and manual task.

## 8. Integration Design

## 8.1 AI service integration

Backend-to-AI integration should be contract-based:

1. backend submits internal job request
2. worker writes artifact
3. worker writes summary metadata
4. worker emits completion event
5. workflow-service advances state

Backend does not parse raw model internals; it consumes structured outputs only.

## 8.2 External system integration

### Keycloak

- token validation at gateway and service level
- roles mapped to backend permissions

### S3 / MinIO

- object write/read via service credentials
- signed URLs only where UI access is needed

### OpenSearch

- projection/indexing only
- rebuildable from PostgreSQL and artifacts

### Sanctions / AML / fraud adapters

- explicit adapter interfaces
- timeouts and retry bounds
- unresolved checks remain `pending`, not passed

### Upstream LOS / onboarding systems

- outbound event or API handoff after approved workflow stage
- never send downstream "approved" if critical compliance is pending

## 8.3 Integration contract versioning

1. Internal payloads must be versioned.
2. Breaking schema changes require dual-read/dual-write or versioned endpoints/topics.
3. Artifact schema version must be stored alongside artifact refs.

## 9. Security Considerations for Backend Services

## 9.1 AuthN / AuthZ

1. OAuth2 / OIDC via Keycloak
2. JWT verification at gateway and service boundary
3. service-to-service auth for internal APIs
4. role-based authorization for review, escalation, and close operations

## 9.2 Data protection

1. TLS in transit for all service traffic
2. encrypted database volumes and object storage
3. scoped service accounts for each backend service
4. secrets managed outside code and rotated

## 9.3 Audit and least privilege

1. every mutating endpoint must log actor identity
2. no backend service may bypass audit write for material actions
3. production services must not have blanket DB superuser access

## 9.4 Sensitive artifact access

1. prompts/responses, OCR artifacts, and review bundles are sensitive
2. access must be role-scoped and traceable
3. signed URLs should be short-lived and least-privileged

## 10. Recommended Backend Build Sequence

1. replace in-memory repository with PostgreSQL repository layer
2. add artifact registry and S3 integration
3. add auth middleware and role enforcement
4. add outbox/event publisher
5. introduce LangGraph extraction workflow service
6. add worker job contracts and queue execution
7. add compliance-state model and separation from case state
8. add OpenSearch projection layer
9. add resilience features, metrics, and DLQ handling

## 11. Recommended Backend Stance

The backend for Ops Agent should behave like a workflow control plane, not just an API layer.

That means:

1. explicit state transitions,
2. durable orchestration,
3. append-only auditability,
4. contract-based AI integrations,
5. visible failure handling.

That is the correct backend operating model for a banking document platform.

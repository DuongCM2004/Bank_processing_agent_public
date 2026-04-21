# Backend Service Decomposition and Workflow Execution Design for Ops Agent

## Current Documents Module Baseline

For document information extraction, use [production-llm-document-extraction-backend-spec.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\production-llm-document-extraction-backend-spec.md) as the current implementation source. The active workflow is FastAPI upload, object storage, async worker dispatch, Python/Pillow preprocessing, LangGraph orchestration, OpenAI GPT-4o or GPT-4o-mini Vision structured JSON extraction, strict schema validation, one retry, manual review, approved-only PostgreSQL persistence, audit trail, and UUID search. Older service splits around OCR model training, classical ML extraction, dataset preparation, benchmarking, or evaluation do not apply to the Documents extraction module.

## Role

Senior Backend Engineer for a banking-grade Document Processing Agent.

## Objective

Define the backend service layer and how services collaborate to process documents safely, with explicit workflow state, asynchronous execution, failure containment, and audit/compliance alignment.

## Assumptions

1. The target platform uses FastAPI, Temporal, Kafka and or Redis, Celery, PostgreSQL, S3 / MinIO, OpenSearch, and Keycloak.
2. The current repo already has an MVP workflow foundation with case creation, document registration, review tasks, corrections, escalations, revalidation, closure, and audit event retrieval.
3. Human review, compliance gating, and auditability are mandatory architectural constraints.
4. Workflow state must remain explicit and durable; it must not be inferred from queue depth or worker logs.
5. Backend design must support a narrow MVP first, then evolve safely toward broader scale.

## Deliverables

- Service list
- Service responsibilities
- Communication model
- Queue and job orchestration
- Case state machine
- Retry and timeout behavior
- Error handling model
- Observability requirements
- Security-sensitive behaviors
- MVP service layout
- Scale-stage split plan

## Dependencies

1. [solution-architecture-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\solution-architecture-blueprint.md)
2. [backend-engineering-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\backend-engineering-blueprint.md)
3. [api-specification.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\api-specification.md)
4. [database-persistence-schema.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\database-persistence-schema.md)
5. [ai-architecture.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ai-architecture.md)
6. [compliance-risk-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\compliance-risk-controls.md)

## Risks

1. Hidden coupling between synchronous APIs and asynchronous workflow execution.
2. Invalid state transitions caused by services updating shared state without workflow coordination.
3. Duplicate side effects caused by retries without idempotency discipline.
4. Compliance state being treated as advisory instead of a hard gate.
5. Over-splitting services too early and increasing delivery and support overhead.

## MVP vs Scale Notes

### MVP

1. Keep service boundaries real, but deploy them as a small platform estate.
2. Prefer one repository with modular service packages over many independently managed repos.
3. Keep orchestration explicit with Temporal and keep heavy compute off the request path.
4. Ship human review, audit, and compliance visibility before advanced optimization.

### Scale

1. Split services further only when team ownership, throughput, or release cadence justifies it.
2. Add higher isolation for review, compliance, and AI-heavy workloads when load or risk requires it.
3. Add HA, regional failover, and more specialized worker pools after core semantics stabilize.

## 1. Service List

| Service | Type | Primary purpose |
|---|---|---|
| `api-gateway` | edge | routing, auth forwarding, throttling |
| `case-service` | control plane | case lifecycle, current state, case reads |
| `ingestion-service` | control plane | document intake, file registration, storage metadata |
| `workflow-service` | orchestration control plane | Temporal workflow start, signals, status |
| `review-service` | control plane | review task management and manual actions |
| `compliance-service` | control plane | control status evaluation and compliance gates |
| `decision-service` | control plane | route selection and next-action gating |
| `audit-service` | control plane | immutable audit write and retrieval |
| `artifact-service` | support service | signed artifact access and artifact metadata resolution |
| `ocr-worker` | async compute | OCR preprocessing and VietOCR execution |
| `layout-worker` | async compute | page and region parsing |
| `classification-worker` | async compute | document type inference |
| `extraction-worker` | async compute | field extraction and reconciliation |
| `validation-worker` | async compute | rules execution and cross-document checks |
| `notification-service` | future support service | reviewer and system notifications |

## 2. Responsibility of Each Service

### 2.1 `api-gateway`

1. Validate bearer tokens at the edge.
2. Forward trusted identity context.
3. Apply rate limits and request size constraints.
4. Route public and internal traffic to the right service boundary.

### 2.2 `case-service`

1. Own the `cases` resource and current workflow-visible case state.
2. Serve case metadata to frontend and internal services.
3. Enforce workflow-safe mutations on case-level operations.
4. Publish case-related domain events via outbox.

### 2.3 `ingestion-service`

1. Accept document metadata and upload registration.
2. Validate intake payloads and basic file-policy checks.
3. Create document and document-version records.
4. Store raw artifact metadata and emit intake events.

### 2.4 `workflow-service`

1. Start and manage Temporal workflows.
2. Coordinate per-case and per-document execution steps.
3. Pause on human review and resume on reviewer signals.
4. Keep orchestration semantics out of individual worker implementations.

### 2.5 `review-service`

1. Create and manage review tasks.
2. Accept claim, correction, escalation, revalidation, and close actions.
3. Enforce role-based action permissions and required reason codes.
4. Ensure reviewer actions produce audit events and state transitions.

### 2.6 `compliance-service`

1. Evaluate workflow-level compliance control status.
2. Persist control outcomes and pending check states.
3. Block unsafe progression when critical checks are pending, failed, or escalated.
4. Surface specialist-review requirements.

### 2.7 `decision-service`

1. Aggregate upstream outputs into the next permitted route.
2. Apply conservative policy thresholds and hard gates.
3. Decide only workflow routing, not final human-owned outcomes.
4. Produce structured rationale, reason codes, and route metadata.

### 2.8 `audit-service`

1. Persist immutable audit events.
2. Support case-level and resource-level audit retrieval.
3. Fan out indexed copies to search.
4. Preserve version references for rules, models, prompts, and workflow definitions.

### 2.9 `artifact-service`

1. Resolve artifact metadata and signed access for authorized callers.
2. Abstract raw storage keys from frontend clients.
3. Enforce artifact-level authorization and retention-aware access rules.

### 2.10 Worker services

1. Consume jobs from the orchestration layer or queue fabric.
2. Perform bounded compute work only.
3. Write artifacts and result records durably before reporting completion.
4. Never mutate case state directly.

## 3. How Services Communicate

### 3.1 Communication patterns

| Pattern | Where used | Purpose |
|---|---|---|
| synchronous HTTP | gateway to control-plane services | request-response APIs for UI and upstream systems |
| synchronous internal HTTP | control-plane service to control-plane service | command or read operations where immediate reply is needed |
| Temporal activities and signals | workflow-service to workers and review flows | durable orchestration, wait states, retries |
| async events | outbox to Kafka | domain fan-out, indexing, notifications, observability hooks |
| artifact refs | PostgreSQL plus S3 / MinIO | large artifact exchange without embedding blobs in messages |

### 3.2 Communication rules

1. Public clients talk only to gateway-exposed public APIs.
2. Control-plane services never read each other's private tables directly.
3. Workers receive explicit job payloads and return explicit result payloads.
4. State transitions happen through owned services and workflow coordination, not by side effect.
5. Every cross-service mutation path must carry `trace_id`, actor context where applicable, and version refs.

## 4. Queue and Job Orchestration Approach

### 4.1 Orchestration model

1. Temporal owns long-running workflow execution.
2. Kafka distributes domain events and non-blocking fan-out.
3. Celery executes compute-heavy jobs.
4. PostgreSQL outbox prevents state and event divergence.

### 4.2 Workflow shape

1. Parent workflow per case.
2. Child workflow or step chain per document version.
3. Aggregation step at case level for cross-document validation, compliance, and decisioning.
4. Human review represented as a durable wait state, not a polling loop.

### 4.3 Queue separation

| Queue / topic | Purpose |
|---|---|
| `document.received` | intake accepted |
| `ocr.jobs.gpu` | OCR on GPU |
| `ocr.jobs.cpu` | OCR fallback |
| `layout.jobs` | layout parsing |
| `classification.jobs` | classification |
| `extraction.jobs` | extraction |
| `validation.jobs` | validation |
| `compliance.jobs` | control evaluation |
| `decision.jobs` | route evaluation |
| `review.required` | create review tasks |
| `pipeline.dlq` | dead-letter handling |

### 4.4 Job payload minimum

Every async job payload must include:

1. `trace_id`
2. `case_id`
3. `document_id` when applicable
4. `document_version_id` when applicable
5. `workflow_run_id`
6. `step_name`
7. `attempt_no`
8. `artifact_refs`
9. `version_refs`

## 5. Case State Machine

### 5.1 Canonical states

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

### 5.2 State transition rules

| From | To | Triggering service |
|---|---|---|
| `received` | `stored` | ingestion-service |
| `stored` | `queued` | workflow-service |
| `queued` | `processing` | workflow-service |
| `queued` | `review_required` | decision-service or workflow-service |
| `processing` | `validated` | validation-service via workflow-service |
| `processing` | `failed` | workflow-service after unrecoverable step failure |
| `processing` | `review_required` | decision-service or compliance-service |
| `validated` | `review_required` | compliance-service or decision-service |
| `validated` | `approved` | review-service with authorized actor |
| `validated` | `rejected` | review-service with authorized actor |
| `review_required` | `in_review` | review-service on claim |
| `in_review` | `corrected` | review-service on correction |
| `in_review` | `escalated` | review-service on escalation |
| `in_review` | `approved` | review-service on approval |
| `in_review` | `rejected` | review-service on rejection |
| `corrected` | `validated` | workflow-service after revalidation |
| `corrected` | `review_required` | workflow-service if unresolved |
| `escalated` | `in_review` | review-service when specialist resumes |
| `escalated` | `closed` | review-service on authorized specialist close |
| `approved` | `closed` | review-service close action |
| `rejected` | `closed` | review-service close action |
| `failed` | `review_required` | review-service or workflow-service recovery path |
| `failed` | `closed` | review-service or operations closeout |

### 5.3 State-management rules

1. Only control-plane services may update case state.
2. Workers publish outputs; they do not directly transition case state.
3. Compliance state is separate from operational case state.
4. A case cannot become operationally complete while critical compliance checks remain pending or failed.

## 6. Retry and Timeout Behavior

### 6.1 Retry classes

1. Stateless read or compute step:
   exponential backoff with jitter, max 3 attempts.
2. OCR GPU task:
   2 GPU retries, then 1 CPU retry.
3. External compliance adapter:
   bounded retries, then mark check `pending`.
4. Human-review signal wait:
   no retry loop; use workflow timeout and SLA monitoring instead.

### 6.2 Timeout expectations

1. Public API request timeout should remain short and never wait for full document processing.
2. Worker step timeouts must be explicit per step:
   OCR, layout, extraction, validation, compliance lookup.
3. Temporal activity and workflow timeouts must be configured independently.
4. Stuck review waits are managed by SLA alerts and supervisor workflows, not by auto-close logic.

### 6.3 Retry rules

1. All retries preserve the same `trace_id`.
2. Idempotency keys or deterministic step identifiers prevent duplicate durable writes.
3. A step is complete only after durable state and artifacts are written.
4. Retry exhaustion routes to visible failure handling, not silent abandonment.

## 7. Error Handling Model

### 7.1 Error classes

| Error class | Example | Handling |
|---|---|---|
| request validation error | malformed payload | return `400` or `422`, no retry |
| auth / authz error | missing token, forbidden role | return `401` or `403`, log security event |
| domain conflict | invalid state transition | return `409`, do not retry blindly |
| missing dependency | artifact missing | mark step failed or review-needed depending on step |
| transient infrastructure error | DB timeout, broker timeout | retry with backoff |
| worker capacity error | GPU saturation | retry on overflow queue or CPU fallback |
| external dependency degradation | screening adapter unavailable | mark control pending, block auto-process |

### 7.2 Error response rules

1. Public APIs return machine-readable `error_code`, `message`, `trace_id`, `retryable`, and `details`.
2. Internal job failures store error code and message in workflow-step records.
3. High-severity failures produce audit and observability signals.
4. No internal stack traces are exposed to public clients.

### 7.3 Failure containment strategy

1. Fail one document step without losing the case.
2. Preserve partial outputs where safe and mark unresolved areas explicitly.
3. Route unresolved or failed cases to review rather than forcing completion.
4. Use DLQ for exhausted retries and require explicit replay or manual intervention.

## 8. Observability Requirements

### 8.1 Metrics

1. API latency, error rate, and throughput by service.
2. Queue depth and consumer lag by job type.
3. Workflow success, retry, timeout, and stuck-wait counts.
4. Review queue backlog, claim time, and aging.
5. OCR, extraction, and validation latency and confidence distributions.
6. Audit write failures and evidence-write failures.

### 8.2 Logs

1. Structured JSON logs for all services.
2. Correlate by `trace_id`, `case_id`, `document_id`, and service name.
3. Log reason codes, route outcomes, retry attempts, and authorization failures.
4. Mask or omit sensitive document content from general logs.

### 8.3 Tracing

1. OpenTelemetry traces across gateway, control-plane services, workers, DB calls, and artifact access.
2. Temporal workflow ids and activity ids included in spans.
3. Reviewer actions correlated to the same trace family where feasible.

### 8.4 Alerts

1. Stuck workflows
2. growing DLQ
3. queue lag
4. audit persistence failure
5. compliance adapter outage
6. unusual spikes in review rate or failure rate

## 9. Security-Sensitive Service Behaviors

### 9.1 General rules

1. Least privilege for service credentials.
2. TLS for all service-to-service traffic where supported by deployment.
3. No shared superuser DB access across services.
4. Sensitive artifact access through controlled service endpoints, not raw bucket exposure.

### 9.2 Service-specific security behaviors

#### Ingestion service

1. Treat all uploads as untrusted.
2. Enforce MIME, size, and quarantine policy checks.
3. Do not expose raw storage paths to public clients.

#### Review service

1. Enforce role-based permissions on claim, correction, escalation, approval, rejection, and close.
2. Require reason codes for material actions.
3. Preserve original machine outputs and reviewer actions distinctly.

#### Compliance service

1. Do not flatten pending critical checks into pass outcomes.
2. Do not auto-clear sanctions, AML, or fraud-sensitive states.
3. Log all manual overrides and exception approvals.

#### Audit service

1. Append-only writes.
2. No delete path in production.
3. Restrict full audit export to approved roles.

## 10. MVP Service Layout

### 10.1 MVP runtime stance

1. Deploy a small set of FastAPI services with shared libraries where appropriate.
2. Keep a single workflow-service boundary even if the implementation initially lives inside the main backend package.
3. Use dedicated worker processes for OCR and other async compute.
4. Keep artifact resolution and audit retrieval simple but explicit.

### 10.2 MVP service grouping

Recommended deployable grouping for MVP:

1. `platform-api`
   case-service, ingestion-service, review-service, audit-service
2. `workflow-api`
   workflow-service, compliance-service, decision-service
3. `worker-ai`
   OCR, layout, classification, extraction, validation workers
4. `gateway`
   Kong or Nginx

This keeps boundaries clear without requiring too many independently managed deployables on day one.

## 11. Scale-Stage Refactoring or Service Split Plan

### 11.1 When to split further

Split a service only when at least one of these is true:

1. team ownership diverges materially,
2. throughput or latency characteristics differ sharply,
3. deployment cadence differs enough to justify isolation,
4. security isolation requirements increase.

### 11.2 Recommended scale-stage splits

1. split `audit-service` if audit write throughput or retention policy becomes operationally distinct
2. split `artifact-service` if reviewer traffic and artifact-security controls grow significantly
3. split `compliance-service` into control-evaluation and external-screening adapters if compliance integrations become complex
4. split `worker-ai` into dedicated worker pools by OCR, extraction, and validation load profile
5. add `notification-service` for SLA, reviewer, and downstream event delivery

### 11.3 What should remain stable

Keep these stable even at scale:

1. explicit case state machine
2. workflow-driven coordination
3. append-only audit model
4. evidence-first payloads
5. strict separation between machine recommendation and human-owned final decisions

## 12. Recommended Backend Stance

The backend should be:

1. explicit about workflow state,
2. conservative about routing and completion,
3. asynchronous by default for heavy processing,
4. strict about idempotency and audit side effects,
5. modular enough for parallel team execution without becoming over-fragmented in MVP.

# API Specification for Ops Agent

## Role

Senior Backend Engineer and API Architect for a banking-grade Document Processing Agent.

## Objective

Define the APIs needed for document ingestion, workflow orchestration, review support, result retrieval, and audit access in a form that is practical for implementation and aligned with the repo's current FastAPI workflow model.

## Current API Baseline

The current Documents module API is defined by [production-llm-document-extraction-backend-spec.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\production-llm-document-extraction-backend-spec.md).

The production extraction API is document-UUID centric:

1. `POST /documents/upload`
2. `GET /documents/{uuid}/status`
3. `GET /documents/{uuid}/extraction`
4. `POST /documents/{uuid}/review`
5. `GET /audit/{uuid}`

The extraction API returns asynchronous status and review-ready structured data. It does not expose dataset, training, testing, benchmarking, or model-evaluation resources.

## Assumptions

1. The current MVP backend must support document upload, extraction status retrieval, extraction result retrieval, manual review submission, and audit-event retrieval.
2. PostgreSQL will become the system of record for production, but the current API contract should remain stable while persistence evolves.
3. Asynchronous processing is workflow-driven and must expose visible state rather than hiding work behind synchronous request latency.
4. The API must support both human-review UI needs and internal workflow orchestration.
5. Review edit, approval, and rejection must remain workflow-safe and auditable.

## Deliverables

- API design principles
- AuthN and AuthZ assumptions
- Resources and entities
- Endpoint list
- Request and response shapes
- Status and error design
- Asynchronous patterns
- Case status tracking
- Manual review APIs
- Audit access APIs
- MVP endpoints
- Future scale endpoints

## Dependencies

1. [ops-agent-prd.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ops-agent-prd.md)
2. [solution-architecture-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\solution-architecture-blueprint.md)
3. [backend-engineering-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\backend-engineering-blueprint.md)
4. [ai-architecture.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ai-architecture.md)
5. [frontend-ops-dashboard-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\frontend-ops-dashboard-blueprint.md)
6. [compliance-risk-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\compliance-risk-controls.md)

## Risks

1. API contracts drift away from workflow-safe state transitions.
2. Frontend needs expand faster than backend response models.
3. Async processing details leak into synchronous APIs inconsistently.
4. Internal integration endpoints become de facto public APIs without governance.
5. Audit and evidence access become incomplete or over-broad.

## MVP vs Scale notes

### MVP

1. Keep the public API narrow and case-centric.
2. Expose enough metadata for review, audit, and result retrieval without requiring read access to internal services.
3. Prefer simple polling for workflow progress over early event-stream complexity.

### Scale

1. Add richer query, pagination, filtering, and downstream integration endpoints once the workflow contract is stable.
2. Introduce notification, webhook, and bulk APIs only when operational ownership and idempotency semantics are mature.
3. Keep internal orchestration APIs versioned separately from public APIs.

## 1. API Design Principles

1. Resource-first design
   Public APIs are organized around stable business resources such as cases, documents, review tasks, results, and audit events.
2. Workflow-safe mutation
   Every mutating endpoint must respect the case state machine and reject invalid state transitions explicitly.
3. Explicit async behavior
   Any operation that triggers asynchronous work returns accepted metadata and current processing state rather than pretending the workflow is complete.
4. Conservative payloads
   Responses include the minimum structured data needed by UI and internal integrations, with evidence and reason-code references where required.
5. Auditability by contract
   Mutating APIs are designed so the backend can always attach actor identity, reason codes, trace ids, and workflow events.
6. Stable naming
   Use nouns for resources and action nouns only where the workflow truly requires a command endpoint:
   `claim`, `revalidate`, `close`, `escalate`.

## 2. Authentication and Authorization Assumptions

1. Public and reviewer-facing APIs are protected by OAuth2 / OIDC tokens issued through Keycloak.
2. API gateway validates bearer tokens and forwards trusted identity claims to backend services.
3. Backend services still enforce authorization at the service layer; gateway auth is not sufficient by itself.
4. Internal service-to-service APIs use scoped service credentials and are not exposed directly to browser clients.
5. Role assumptions for MVP:
   `branch_support`, `ops_reviewer`, `compliance_analyst`, `fraud_analyst`, `back_office`, `supervisor`, `platform_admin`.
6. Sensitive artifact and audit retrieval must be role-gated and field-masked where policy requires.

## 3. Main Resources and Entities

### 3.1 Public business resources

| Resource | Purpose | Primary key |
|---|---|---|
| Case | workflow container for one operational document-processing job | `case_id` |
| Document | one uploaded or registered source document under a case | `document_id` |
| Case Results | extraction, validation, and route recommendation for a case | `case_id` |
| Review Task | unit of manual review work | `task_id` |
| Audit Event | immutable record of case-related action | `event_id` |

### 3.2 Internal orchestration resources

| Resource | Purpose | Primary key |
|---|---|---|
| Extraction Run | LangGraph-backed execution state for one document extraction | `extraction_uuid` |
| Job Submission | one compute or rules-processing request | `job_id` |
| Compliance Evaluation | control-status evaluation result | `evaluation_id` |
| Decision Evaluation | route-selection computation result | `decision_id` |

## 4. Shared API Conventions

### 4.1 Headers

| Header | Required | Purpose |
|---|---|---|
| `Authorization: Bearer <token>` | yes for protected APIs | user or service auth |
| `X-Request-Id` | should-have | client request correlation |
| `Idempotency-Key` | should-have on mutating endpoints | safe retry semantics |
| `X-Trace-Id` | optional if caller already has one | workflow correlation |

### 4.2 Response envelope pattern

Public APIs return resource objects directly for simple retrieval and creation. Errors use a standard error body. Mutating async-triggering endpoints return current state plus references to follow-up retrieval endpoints.

### 4.3 Common enums

#### Case status

`received`, `stored`, `queued`, `processing`, `validated`, `review_required`, `in_review`, `corrected`, `approved`, `rejected`, `escalated`, `failed`, `closed`

#### Processing status

`not_started`, `in_progress`, `complete`, `failed`

#### Review task status

`open`, `claimed`, `completed`

## 5. Public Endpoint List

### 5.1 System endpoints

| Method | Path | Purpose | MVP |
|---|---|---|---|
| `GET` | `/health` | liveness probe | yes |
| `GET` | `/ready` | readiness probe for dependencies | future |
| `GET` | `/metrics` | Prometheus metrics | future internal |

### 5.2 Document endpoints

| Method | Path | Purpose | MVP |
|---|---|---|---|
| `POST` | `/documents/upload` | upload document, store raw file, create UUIDs, queue extraction | yes |
| `GET` | `/documents/{uuid}/status` | fetch document and latest extraction status | yes |
| `GET` | `/documents/{uuid}/extraction` | fetch extracted and reviewed fields for table UI | yes |
| `POST` | `/documents/{uuid}/review` | submit reviewer edit, approval, or rejection | yes |
| `GET` | `/documents` | filtered document search/list by UUID/status | future |
| `GET` | `/documents/{uuid}/artifact-link` | fetch signed artifact URL or artifact metadata | future |

### 5.3 Review endpoints

| Method | Path | Purpose | MVP |
|---|---|---|---|
| `POST` | `/documents/{uuid}/review` | edit, approve, or reject reviewed extraction payload | yes |
| `GET` | `/documents/{uuid}/extraction` | retrieve review table state | yes |
| `GET` | `/review/tasks` | list document review tasks by status and queue | future |

### 5.4 Audit endpoints

| Method | Path | Purpose | MVP |
|---|---|---|---|
| `GET` | `/audit/{uuid}` | fetch audit events by document UUID or extraction UUID | yes |
| `GET` | `/audit/events/{event_id}` | fetch one audit event | future |

## 6. Public Request and Response Shapes

### 6.1 `POST /v1/cases`

Purpose:
create a case, register optional initial documents, initialize results, and create initial review work when policy requires it.

Request:

```json
{
  "workflow_type": "kyc_onboarding",
  "priority": "normal",
  "customer_reference": "cust_001",
  "review_required": true,
  "documents": [
    {
      "filename": "passport.pdf",
      "mime_type": "application/pdf",
      "source_channel": "manual_upload",
      "retention_class": "bank_ops_default"
    }
  ]
}
```

Response `201 Created`:

```json
{
  "case": {
    "case_id": "case_123",
    "workflow_type": "kyc_onboarding",
    "priority": "normal",
    "customer_reference": "cust_001",
    "status": "review_required",
    "review_required": true,
    "assigned_queue": "ops_review",
    "created_at": "2026-04-14T11:00:00Z",
    "updated_at": "2026-04-14T11:00:00Z",
    "document_ids": ["doc_123"],
    "review_task_ids": ["review_task_123"],
    "final_outcome": null
  },
  "documents": [
    {
      "document_id": "doc_123",
      "case_id": "case_123",
      "filename": "passport.pdf",
      "mime_type": "application/pdf",
      "source_channel": "manual_upload",
      "retention_class": "bank_ops_default",
      "file_hash": "sha256hex",
      "status": "not_started",
      "created_at": "2026-04-14T11:00:00Z"
    }
  ],
  "review_tasks": [
    {
      "task_id": "review_task_123",
      "case_id": "case_123",
      "status": "open",
      "assigned_to": null,
      "assigned_queue": "ops_review",
      "reason_codes": ["mvp_default_review_gate"],
      "created_at": "2026-04-14T11:00:00Z",
      "updated_at": "2026-04-14T11:00:00Z"
    }
  ]
}
```

Behavior:

1. Case creation is synchronous, but downstream processing remains asynchronous.
2. Initial status may already be `review_required` if the workflow requires human review by default.
3. If the caller retries with the same idempotency key, the API should return the already-created case rather than creating a duplicate.

### 6.2 `GET /v1/cases/{case_id}`

Purpose:
retrieve the canonical case record for status tracking, queue context, and UI navigation.

Response `200 OK`:

```json
{
  "case_id": "case_123",
  "workflow_type": "kyc_onboarding",
  "priority": "normal",
  "customer_reference": "cust_001",
  "status": "in_review",
  "review_required": true,
  "assigned_queue": "ops_review",
  "created_at": "2026-04-14T11:00:00Z",
  "updated_at": "2026-04-14T11:10:00Z",
  "document_ids": ["doc_123", "doc_124"],
  "review_task_ids": ["review_task_123"],
  "final_outcome": null
}
```

### 6.3 `POST /v1/cases/{case_id}/documents`

Purpose:
attach additional documents to a case that is still open and eligible for document intake.

Request:

```json
{
  "filename": "utility_bill.pdf",
  "mime_type": "application/pdf",
  "source_channel": "branch_upload",
  "retention_class": "bank_ops_default"
}
```

Response `201 Created`:

```json
{
  "document_id": "doc_124",
  "case_id": "case_123",
  "filename": "utility_bill.pdf",
  "mime_type": "application/pdf",
  "source_channel": "branch_upload",
  "retention_class": "bank_ops_default",
  "file_hash": "sha256hex",
  "status": "not_started",
  "created_at": "2026-04-14T11:12:00Z"
}
```

Failure expectations:

1. Return `409 case_closed` if the case is closed.
2. Return `404 case_not_found` if the case does not exist.
3. In production, this endpoint should enqueue downstream document processing and emit a document-received event.

### 6.4 `GET /v1/cases/{case_id}/documents/{document_id}`

Purpose:
retrieve document metadata for review and evidence access.

Response `200 OK`:

```json
{
  "document_id": "doc_124",
  "case_id": "case_123",
  "filename": "utility_bill.pdf",
  "mime_type": "application/pdf",
  "source_channel": "branch_upload",
  "retention_class": "bank_ops_default",
  "file_hash": "sha256hex",
  "status": "in_progress",
  "created_at": "2026-04-14T11:12:00Z"
}
```

### 6.5 `GET /v1/cases/{case_id}/results`

Purpose:
retrieve the current machine-produced results needed for UI review and downstream integration.

Response `200 OK`:

```json
{
  "case_id": "case_123",
  "extraction_status": "complete",
  "validation_status": "complete",
  "fields": [
    {
      "field_name": "full_name",
      "value": "NGUYEN VAN A",
      "normalized_value": "NGUYEN VAN A",
      "confidence": 0.97,
      "required": true,
      "evidence_refs": [
        {
          "document_id": "doc_123",
          "page_number": 1,
          "text_span": "NGUYEN VAN A",
          "bounding_box": {
            "x": 0.1,
            "y": 0.2,
            "width": 0.4,
            "height": 0.08
          }
        }
      ],
      "reason_code": null
    }
  ],
  "validations": [
    {
      "rule_id": "kyc.id.expiry_valid",
      "rule_version": "1.0.0",
      "result": "pass",
      "severity": "info",
      "reason_code": "valid_document",
      "evidence_refs": []
    }
  ],
  "recommended_route": "review_required"
}
```

Behavior:

1. If processing is still running, `extraction_status` and `validation_status` show progress explicitly.
2. This endpoint must never flatten pending compliance into a pass condition.
3. For future versions, compliance summaries may be added either to this response or a dedicated compliance subresource.

### 6.6 `GET /v1/review-tasks`

Purpose:
list manual review tasks for reviewers, supervisors, and specialist queues.

Query parameters:

| Name | Type | MVP | Purpose |
|---|---|---|---|
| `status` | string | yes | filter by `open`, `claimed`, `completed` |
| `assigned_queue` | string | future | filter by queue |
| `assigned_to` | string | future | filter by reviewer |
| `priority` | string | future | filter by case priority |
| `limit` | integer | future | pagination |
| `cursor` | string | future | pagination |

Response `200 OK`:

```json
{
  "items": [
    {
      "task_id": "review_task_123",
      "case_id": "case_123",
      "status": "open",
      "assigned_to": null,
      "assigned_queue": "ops_review",
      "reason_codes": ["mvp_default_review_gate"],
      "created_at": "2026-04-14T11:00:00Z",
      "updated_at": "2026-04-14T11:00:00Z"
    }
  ]
}
```

### 6.7 `POST /v1/review-tasks/{task_id}/claim`

Purpose:
assign a task to a reviewer and transition the case into active review where valid.

Request:

```json
{
  "reviewer_id": "reviewer_007"
}
```

Response `200 OK`:

```json
{
  "task_id": "review_task_123",
  "case_id": "case_123",
  "status": "claimed",
  "assigned_to": "reviewer_007",
  "assigned_queue": "ops_review",
  "reason_codes": ["mvp_default_review_gate"],
  "created_at": "2026-04-14T11:00:00Z",
  "updated_at": "2026-04-14T11:20:00Z"
}
```

Workflow-safe behavior:

1. Claim is allowed only for `open` and, if policy allows, reclaimable `claimed` tasks.
2. Invalid task states return `409 invalid_task_state`.
3. If the case was `review_required`, successful claim transitions it to `in_review`.

### 6.8 `POST /v1/cases/{case_id}/field-corrections`

Purpose:
record reviewer-confirmed corrections without deleting original machine outputs.

Request:

```json
{
  "reviewer_id": "reviewer_007",
  "comment": "OCR dropped trailing character",
  "corrections": [
    {
      "field_name": "full_name",
      "new_value": "NGUYEN VAN AN",
      "reason_code": "reviewer_confirmed_typo",
      "evidence_refs": [
        {
          "document_id": "doc_123",
          "page_number": 1,
          "text_span": "NGUYEN VAN AN"
        }
      ]
    }
  ]
}
```

Response `200 OK`:
returns the updated case resource.

Workflow-safe behavior:

1. The service appends corrected field results rather than overwriting history.
2. Successful correction transitions the case to `corrected`.
3. Corrections must include `reason_code`.

### 6.9 `POST /v1/cases/{case_id}/escalations`

Purpose:
move a case into a specialist review path such as compliance or fraud.

Request:

```json
{
  "reviewer_id": "reviewer_007",
  "escalation_target": "compliance_review",
  "reason_code": "identity_mismatch",
  "comment": "DOB mismatch between passport and application form"
}
```

Response `200 OK`:
returns the updated case resource.

Workflow-safe behavior:

1. Successful escalation transitions the case to `escalated`.
2. Escalation payload must be retained in action history and audit history.
3. Role checks must prevent unauthorized users from escalating to restricted queues if policy requires.

### 6.10 `POST /v1/cases/{case_id}/revalidate`

Purpose:
trigger rerun of downstream validations after manual correction or additional document intake.

Request:

```json
{
  "requested_by": "reviewer_007",
  "reason_code": "corrections_completed"
}
```

Response `200 OK`:
returns the updated case resource.

Behavior:

1. Validation status transitions to `in_progress` then to `complete` when the revalidation workflow finishes.
2. In the current repo implementation this is immediate; in production it should be asynchronous with explicit status tracking.
3. Successful revalidation must emit audit and review-action records.

### 6.11 `POST /v1/cases/{case_id}/close`

Purpose:
finalize the case outcome when allowed by policy and current state.

Request:

```json
{
  "requested_by": "compliance_001",
  "outcome": "approved",
  "reason_code": "all_required_checks_completed"
}
```

Allowed `outcome` values:

`approved`, `rejected`, `closed_without_decision`

Response `200 OK`:
returns the updated case resource with `status="closed"` and `final_outcome` set.

Workflow-safe behavior:

1. Invalid outcomes return `422 invalid_close_outcome`.
2. Under the current state machine, close internally transitions through `approved` or `rejected` first when applicable, then to `closed`.
3. Production authorization must ensure only approved roles can close with particular outcomes.

### 6.12 `GET /v1/cases/{case_id}/audit-events`

Purpose:
retrieve immutable case-level audit history for UI review, compliance, and investigation.

Response `200 OK`:

```json
{
  "items": [
    {
      "event_id": "audit_123",
      "case_id": "case_123",
      "resource_type": "case",
      "resource_id": "case_123",
      "action": "case_state_changed",
      "actor_type": "user",
      "actor_id": "reviewer_007",
      "occurred_at": "2026-04-14T11:25:00Z",
      "details": {
        "new_status": "corrected",
        "reason_code": "field_corrections_recorded"
      }
    }
  ]
}
```

## 7. Status and Error Response Design

### 7.1 Success status codes

| Code | Usage |
|---|---|
| `200 OK` | successful read or command completion |
| `201 Created` | resource creation such as case or document |
| `202 Accepted` | future async submission endpoints where processing starts later |

### 7.2 Failure status codes

| Code | Usage |
|---|---|
| `400 Bad Request` | malformed payload or invalid query param |
| `401 Unauthorized` | missing or invalid token |
| `403 Forbidden` | authenticated but not allowed |
| `404 Not Found` | resource missing or not visible to caller |
| `409 Conflict` | invalid workflow transition or non-claimable task |
| `422 Unprocessable Entity` | domain-valid JSON but invalid semantic value |
| `429 Too Many Requests` | gateway throttling |
| `500 Internal Server Error` | unexpected server failure |
| `503 Service Unavailable` | major dependency unavailable |

### 7.3 Standard error body

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

Design rules:

1. `error_code` is stable and machine-readable.
2. `message` is human-readable but not relied on by clients.
3. `retryable` tells callers whether safe retry is appropriate.
4. `details` contains resource ids and validation context, but no stack traces.

## 8. Asynchronous Processing Patterns

### 8.1 Public async pattern

1. Public create or mutate endpoints acknowledge accepted workflow state quickly.
2. Long-running OCR, extraction, validation, compliance, and decision work runs asynchronously.
3. Clients poll `GET /v1/cases/{case_id}` and `GET /v1/cases/{case_id}/results` for progress in MVP.

### 8.2 Internal async pattern

1. Ingestion emits workflow-start events.
2. Workflow service starts the LangGraph-backed extraction run.
3. Worker jobs are submitted with stable job identity and version refs.
4. Completion of internal jobs updates durable state before route changes are exposed publicly.

### 8.3 Future async enhancements

1. Webhook callbacks for upstream systems
2. Server-sent events or websocket status streams for reviewer UI
3. Bulk workflow submission and batch status retrieval

## 9. Case Status Tracking

### 9.1 Canonical case states

| State | Meaning | Publicly visible |
|---|---|---|
| `received` | case created and accepted | yes |
| `stored` | initial documents registered and stored | yes |
| `queued` | ready for processing | yes |
| `processing` | async processing running | yes |
| `validated` | validation completed successfully | yes |
| `review_required` | human review needed before progress | yes |
| `in_review` | task actively claimed | yes |
| `corrected` | reviewer corrections recorded | yes |
| `approved` | pre-close approval state | internal/public as needed |
| `rejected` | pre-close rejection state | internal/public as needed |
| `escalated` | specialist review path active | yes |
| `failed` | system processing failure | yes |
| `closed` | workflow complete | yes |

### 9.2 Transition safety rules

1. Public command endpoints must never skip required intermediate states silently.
2. Invalid transitions return `409 invalid_state_transition`.
3. Public status must reflect durable workflow state, not transient in-memory computation.
4. Cases with pending critical compliance checks must not surface as complete or ready for final approval.

## 10. Manual Review APIs

### 10.1 Core manual-review commands in MVP

1. list tasks
2. claim task
3. submit field corrections
4. escalate case
5. revalidate case
6. close case

### 10.2 Minimum payload expectations for frontend

Frontend and reviewer flows require:

1. case identity and queue state
2. document metadata and artifact references
3. extracted fields with confidence and evidence refs
4. validation results with severity and reason codes
5. current review-task assignment state
6. audit history and latest review actions

### 10.3 Future review endpoints

1. `POST /v1/review-tasks/{task_id}/release`
2. `POST /v1/review-tasks/{task_id}/reassign`
3. `POST /v1/cases/{case_id}/request-documents`
4. `GET /v1/cases/{case_id}/review-bundle`

## 11. Audit Access APIs

### 11.1 MVP audit access

1. `GET /v1/cases/{case_id}/audit-events`
2. audit events returned in chronological order
3. event body includes actor, resource, action, timestamp, and structured details

### 11.2 Future audit access

1. paginated audit query by case, actor, date range, and action type
2. immutable event export for regulator or audit review
3. review-action API separated from generic audit-event API

## 12. Internal Endpoint Specification

These endpoints are not for browser clients. They are used by orchestration and internal services.

### 12.1 Workflow endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/internal/workflows/start` | start case workflow |
| `POST` | `/internal/workflows/{case_id}/signal-review-complete` | resume after manual review |
| `GET` | `/internal/workflows/{case_id}` | inspect workflow execution state |

Minimal request for workflow start:

```json
{
  "trace_id": "uuid",
  "case_id": "case_123",
  "workflow_type": "kyc_onboarding",
  "document_ids": ["doc_123"],
  "version_refs": {
    "workflow_version": "1.0.0"
  }
}
```

### 12.2 AI and rules job endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/internal/ocr/jobs` | submit OCR job |
| `POST` | `/internal/layout/jobs` | submit layout job |
| `POST` | `/internal/classification/jobs` | submit classification job |
| `POST` | `/internal/extraction/jobs` | submit extraction job |
| `POST` | `/internal/validation/jobs` | submit validation job |
| `POST` | `/internal/compliance/evaluate` | evaluate compliance controls |
| `POST` | `/internal/decision/evaluate` | compute route |

Minimal internal job contract:

```json
{
  "trace_id": "uuid",
  "case_id": "case_123",
  "document_id": "doc_123",
  "workflow_run_id": "wf_123",
  "attempt_no": 1,
  "producer_service": "workflow_service",
  "artifact_refs": {
    "source_document_ref": "s3://bucket/raw/doc_123.pdf"
  },
  "version_refs": {
    "schema_version": "1.0.0",
    "rule_pack_version": "1.0.0"
  }
}
```

## 13. Failure Handling Expectations

1. Public APIs must fail fast on validation, authorization, and invalid transition errors.
2. Retryable downstream failure should usually not fail the initial case-creation request once durable intake has completed.
3. Async failures must surface through:
   case status, results status, audit events, metrics, and DLQ / incident mechanisms.
4. No endpoint may claim completion of processing if required async steps are still pending or failed.

## 14. MVP Endpoints

### Public MVP endpoints

1. `GET /health`
2. `POST /documents/upload`
3. `GET /documents/{uuid}/status`
4. `GET /documents/{uuid}/extraction`
5. `POST /documents/{uuid}/review`
6. `GET /audit/{uuid}`

### Internal MVP endpoints

1. `/internal/workflows/start`
2. `/internal/documents/{document_uuid}/extract`
3. `/internal/extractions/{extraction_uuid}/status`
4. `/internal/preprocessing/jobs`
5. `/internal/extraction/jobs`
6. `/internal/validation/jobs`
7. `/internal/normalization/jobs`

## 15. Future Endpoints for Scale

### Public scale endpoints

1. `GET /v1/cases`
2. `GET /v1/cases/{case_id}/status`
3. `GET /v1/cases/{case_id}/documents`
4. `GET /v1/review-tasks/{task_id}`
5. `POST /v1/review-tasks/{task_id}/release`
6. `POST /v1/review-tasks/{task_id}/reassign`
7. `GET /v1/cases/{case_id}/review-actions`
8. `GET /v1/audit-events/{event_id}`
9. `POST /v1/cases/bulk`
10. `POST /v1/callback-subscriptions`

### Internal scale endpoints

1. job status inspection endpoints by `job_id`
2. workflow replay or recovery endpoints gated to operators
3. downstream handoff endpoints for LOS, onboarding, and records systems
4. signed evidence-link broker endpoints
5. notification and webhook dispatch endpoints

## 16. Recommended API Stance

The API should remain:

1. case-centric,
2. workflow-safe,
3. explicit about async state,
4. conservative in what it exposes,
5. rich enough for reviewer UI and downstream integration without leaking internal coupling.

# Production Backend Specification: LLM-Based Document Information Extraction

## 1. Overview

This document defines the production backend design for the Documents module. The system extracts structured information from identity-card-like document images and PDFs using a Vision-capable LLM.

This is an inference-only workflow. It does not include dataset download, dataset preparation, train/validation/test splits, model training, model benchmarking, or model evaluation. The backend uses OpenAI GPT-4o or GPT-4o-mini for OCR-like visual reading and semantic extraction, with strict structured JSON output.

Core runtime behavior:

1. A user uploads a document image or PDF.
2. The backend stores the raw file in object storage.
3. An asynchronous extraction job is created.
4. The preprocessing service validates, resizes, and encodes the image with Python, Pillow, and base64 data URLs.
5. LangGraph orchestrates the extraction state machine.
6. The LLM adapter calls OpenAI GPT-4o or GPT-4o-mini with the document image and a strict JSON schema.
7. The validation layer checks the output using Pydantic or JSON Schema.
8. The retry handler retries once with a stricter prompt if validation fails.
9. The normalization layer converts structured JSON into tabular data for review.
10. A reviewer edits, approves, or rejects the result.
11. Only approved reviewed data is persisted into production relational tables.
12. Every document, extraction run, review action, and audit event is searchable by UUID.

## 2. System Architecture

### Components

| Component | Responsibility | Required stack |
|---|---|---|
| API Gateway | Ingress, authentication, authorization, rate limits, request correlation | FastAPI behind gateway or reverse proxy |
| Document Upload Service | Accept files, validate metadata, create document UUID, register upload | FastAPI, Pydantic |
| Storage Layer | Store raw files, preprocessed images, raw LLM payloads, normalized artifacts | S3, Azure Blob, or GCP Storage |
| Preprocessing Service | Validate images, render PDF pages, resize, convert to RGB, encode to base64 data URL | Python, Pillow |
| Extraction Orchestrator | Coordinate preprocessing, LLM call, validation, retry, normalization, output | LangGraph |
| LLM Adapter | Call OpenAI GPT-4o or GPT-4o-mini with vision input and structured output | OpenAI Responses API, optional LangChain wrapper |
| Validation Layer | Enforce strict schema, no extra fields, all required fields, null for unknown | Pydantic or JSON Schema |
| Retry Handler | Retry once on schema or parse validation failure with stricter prompt | LangGraph node |
| Manual Review Service | Display extracted fields in editable table; approve or reject | FastAPI + React UI |
| Persistence Layer | Store document metadata, extraction runs, staged data, reviewed data, audit events | PostgreSQL |
| Audit Trail Service | Write append-only lifecycle and review events | PostgreSQL, event-based logging |
| UUID Search Service | Find documents and extraction runs by UUID and reconstruct lifecycle | PostgreSQL indexes, optional OpenSearch projection |

### Architecture Diagram

```text
User / Reviewer UI
  -> API Gateway / FastAPI
  -> Document Upload Service
  -> Object Storage
  -> Async Queue / Background Worker
  -> Preprocessing Service
  -> LangGraph Extraction Orchestrator
       -> preprocess_node
       -> extraction_node
       -> validation_node
       -> retry_node
       -> normalization_node
       -> output_node
  -> OpenAI GPT-4o / GPT-4o-mini Vision
  -> PostgreSQL staging tables
  -> Manual Review Service
  -> PostgreSQL production tables
  -> Audit Trail Service
  -> UUID Search Service
```

## 3. End-to-End Flow

1. User uploads a document through `POST /documents/upload`.
2. API validates file type, file size, request identity, and authorization.
3. Backend generates `document_uuid`.
4. Raw file is stored in object storage under a UUID-based key.
5. A `documents` row is created with status `uploaded`.
6. An `extraction_runs` row is created with `extraction_uuid`.
7. Audit event `document.uploaded` is written.
8. Extraction job is queued through Celery, Redis Queue, or equivalent background workers.
9. Status changes to `queued`.
10. Worker starts LangGraph pipeline and sets status `preprocessing`.
11. Preprocessing validates image readability or renders PDF pages.
12. Image is resized, converted to RGB, compressed, and encoded as base64 data URL.
13. Status changes to `extracting`.
14. LLM Adapter calls OpenAI GPT-4o or GPT-4o-mini with the image and strict schema.
15. Raw LLM response is stored as an immutable artifact.
16. Status changes to `validating`.
17. Validation layer checks the response against strict schema rules.
18. If valid, output is canonicalized and status becomes `extracted`.
19. If invalid, status becomes `retrying` and the retry handler runs one stricter LLM call.
20. Retry output is validated.
21. If retry succeeds, output is canonicalized and status becomes `extracted`.
22. If retry fails, status becomes `failed` or `in_review` according to product policy.
23. Normalization converts structured JSON into table rows.
24. Staged extracted data is stored.
25. Status changes to `in_review`.
26. UI displays raw document preview and editable extracted-field table.
27. Reviewer edits, approves, or rejects.
28. Review edits and decisions are stored in review logs.
29. If approved, reviewed data is written to production relational tables.
30. Status changes to `persisted`.
31. All events are linked by `document_uuid` and `extraction_uuid`.

Flow summary:

```text
Upload -> Store -> Queue -> Preprocess -> Extract -> Validate -> Retry
-> Normalize -> Table -> Review -> Approve -> Persist -> Audit
```

## 4. Extraction Schema

All fields are required. Unknown values must be `null`. Empty strings are normalized to `null`. No additional fields are allowed.

```json
{
  "type": "object",
  "properties": {
    "document_type": { "type": ["string", "null"] },
    "full_name": { "type": ["string", "null"] },
    "first_name": { "type": ["string", "null"] },
    "last_name": { "type": ["string", "null"] },
    "id_number": { "type": ["string", "null"] },
    "document_number": { "type": ["string", "null"] },
    "date_of_birth": { "type": ["string", "null"] },
    "sex": { "type": ["string", "null"] },
    "gender": { "type": ["string", "null"] },
    "nationality": { "type": ["string", "null"] },
    "place_of_birth": { "type": ["string", "null"] },
    "issue_date": { "type": ["string", "null"] },
    "expiry_date": { "type": ["string", "null"] },
    "issuing_authority": { "type": ["string", "null"] },
    "address": { "type": ["string", "null"] },
    "raw_full_text": { "type": ["string", "null"] }
  },
  "required": [
    "document_type",
    "full_name",
    "first_name",
    "last_name",
    "id_number",
    "document_number",
    "date_of_birth",
    "sex",
    "gender",
    "nationality",
    "place_of_birth",
    "issue_date",
    "expiry_date",
    "issuing_authority",
    "address",
    "raw_full_text"
  ],
  "additionalProperties": false
}
```

Extraction rules:

1. Return only the JSON object defined by the schema.
2. Use `null` for missing, unclear, occluded, unsupported, or uncertain fields.
3. Do not hallucinate values.
4. Preserve visible text exactly where possible.
5. `document_type` may be inferred only as a short label such as `national_id`, `passport`, `driver_license`, `resident_card`, or `null`.
6. `raw_full_text` is a best-effort plain-text transcription of visible document text.

## 5. LangGraph Pipeline Design

### State

```python
class ExtractionState(TypedDict, total=False):
    document_uuid: str
    extraction_uuid: str
    file_uri: str
    page_number: int | None
    image_data_url: str | None
    preprocessed_image_uri: str | None
    model_name: str
    prompt_version: str
    schema_version: str
    prediction: dict[str, str | None]
    raw_llm_response_uri: str | None
    is_valid: bool
    validation_errors: list[str]
    attempts: int
    status: str
    normalized_payload: dict
    error_code: str | None
    error_message: str | None
```

### Nodes

| Node | Responsibility |
|---|---|
| `preprocess_node` | Load raw file, validate image, render PDF if needed, resize, encode as base64 data URL |
| `extraction_node` | Call GPT-4o or GPT-4o-mini Vision with strict JSON schema |
| `validation_node` | Validate output with Pydantic or JSON Schema |
| `retry_node` | Retry once with stricter prompt when validation fails |
| `normalization_node` | Canonicalize JSON and flatten into tabular review format |
| `output_node` | Persist final run state, emit audit events, set review or failure status |

### Edges

```text
START
-> preprocess_node
-> extraction_node
-> validation_node
-> if valid: normalization_node
-> if invalid and attempts < 2: retry_node
-> if invalid and attempts >= 2: output_node
retry_node -> validation_node
normalization_node -> output_node
output_node -> END
```

### Retry Routing

```python
def route_after_validation(state: ExtractionState) -> str:
    if state.get("is_valid") is True:
        return "normalize"
    if state.get("attempts", 0) < 2:
        return "retry"
    return "finalize_failed"
```

## 6. State Machine

| Status | Meaning |
|---|---|
| `uploaded` | Raw document accepted and stored |
| `queued` | Extraction job created and waiting for worker |
| `preprocessing` | File is being validated, rendered, resized, and encoded |
| `extracting` | LLM extraction is running |
| `validating` | Structured output is being validated |
| `retrying` | One retry is running after validation failure |
| `extracted` | Valid structured extraction is available |
| `in_review` | Extracted data is waiting for human review |
| `approved` | Reviewer approved the final reviewed data |
| `rejected` | Reviewer rejected the extraction |
| `persisted` | Approved data has been written to production tables |
| `failed` | Extraction failed due to file, model, validation, or system error |

Allowed transitions:

```text
uploaded -> queued
queued -> preprocessing
preprocessing -> extracting
extracting -> validating
validating -> extracted
validating -> retrying
retrying -> validating
validating -> failed
extracted -> in_review
in_review -> approved
in_review -> rejected
approved -> persisted
```

## 7. Manual Review System

The review UI displays the raw document preview beside an editable table of extracted fields.

Required table columns:

| Column | Description |
|---|---|
| Field | Schema field name |
| Extracted Value | LLM-produced value |
| Reviewed Value | Editable reviewer-confirmed value |
| Validation Status | valid, missing, edited, rejected, invalid |
| Last Edited By | Reviewer UUID |
| Last Edited At | Timestamp |

Reviewer actions:

1. `edit`: change one or more field values.
2. `approve`: approve the reviewed payload.
3. `reject`: reject extraction with a reason.

Rules:

1. Reviewer edits never overwrite raw LLM output.
2. Every edit logs previous value, new value, reviewer UUID, timestamp, and reason where required.
3. Approved reviewed payload must pass the strict schema before persistence.
4. Only approved reviewed data is persisted into production tables.
5. Rejected data remains traceable but is not persisted as authoritative business data.

## 8. Database Design

Database: PostgreSQL.

UUIDs:

1. `document_uuid` identifies every uploaded document.
2. `extraction_uuid` identifies every extraction run.
3. `audit_event_uuid` identifies every audit event.

### `documents`

Stores uploaded document metadata and current lifecycle status.

```sql
CREATE TABLE documents (
    id BIGSERIAL PRIMARY KEY,
    document_uuid UUID NOT NULL UNIQUE,
    uploaded_by_user_uuid UUID NOT NULL,
    original_filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    page_count INTEGER,
    raw_file_uri TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN (
            'uploaded','queued','preprocessing','extracting','validating',
            'retrying','extracted','in_review','approved','rejected',
            'persisted','failed'
        )
    ),
    failure_code TEXT,
    failure_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_documents_document_uuid ON documents(document_uuid);
CREATE INDEX idx_documents_status ON documents(status);
```

### `extraction_runs`

Stores model, prompt, schema, retry, status, and validation metadata.

```sql
CREATE TABLE extraction_runs (
    id BIGSERIAL PRIMARY KEY,
    extraction_uuid UUID NOT NULL UNIQUE,
    document_uuid UUID NOT NULL REFERENCES documents(document_uuid),
    model_name TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN (
            'queued','preprocessing','extracting','validating',
            'retrying','extracted','in_review','failed'
        )
    ),
    attempts INTEGER NOT NULL DEFAULT 0,
    raw_llm_response_uri TEXT,
    normalized_payload_uri TEXT,
    validation_errors JSONB,
    failure_code TEXT,
    failure_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_extraction_runs_extraction_uuid ON extraction_runs(extraction_uuid);
CREATE INDEX idx_extraction_runs_document_uuid ON extraction_runs(document_uuid);
CREATE INDEX idx_extraction_runs_status ON extraction_runs(status);
```

### `extracted_data`

Stores machine output and reviewer-approved staged output.

```sql
CREATE TABLE extracted_data (
    id BIGSERIAL PRIMARY KEY,
    extracted_data_uuid UUID NOT NULL UNIQUE,
    document_uuid UUID NOT NULL REFERENCES documents(document_uuid),
    extraction_uuid UUID NOT NULL REFERENCES extraction_runs(extraction_uuid),
    extracted_payload JSONB NOT NULL,
    reviewed_payload JSONB,
    document_type TEXT,
    full_name TEXT,
    first_name TEXT,
    last_name TEXT,
    id_number TEXT,
    document_number TEXT,
    date_of_birth TEXT,
    sex TEXT,
    gender TEXT,
    nationality TEXT,
    place_of_birth TEXT,
    issue_date TEXT,
    expiry_date TEXT,
    issuing_authority TEXT,
    address TEXT,
    raw_full_text TEXT,
    reviewed_document_type TEXT,
    reviewed_full_name TEXT,
    reviewed_first_name TEXT,
    reviewed_last_name TEXT,
    reviewed_id_number TEXT,
    reviewed_document_number TEXT,
    reviewed_date_of_birth TEXT,
    reviewed_sex TEXT,
    reviewed_gender TEXT,
    reviewed_nationality TEXT,
    reviewed_place_of_birth TEXT,
    reviewed_issue_date TEXT,
    reviewed_expiry_date TEXT,
    reviewed_issuing_authority TEXT,
    reviewed_address TEXT,
    reviewed_raw_full_text TEXT,
    review_status TEXT NOT NULL DEFAULT 'pending' CHECK (
        review_status IN ('pending','edited','approved','rejected')
    ),
    approved_by_user_uuid UUID,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_extracted_data_document_uuid ON extracted_data(document_uuid);
CREATE INDEX idx_extracted_data_extraction_uuid ON extracted_data(extraction_uuid);
CREATE INDEX idx_extracted_data_review_status ON extracted_data(review_status);
```

### `review_logs`

Stores edits and review decisions.

```sql
CREATE TABLE review_logs (
    id BIGSERIAL PRIMARY KEY,
    review_log_uuid UUID NOT NULL UNIQUE,
    document_uuid UUID NOT NULL REFERENCES documents(document_uuid),
    extraction_uuid UUID NOT NULL REFERENCES extraction_runs(extraction_uuid),
    reviewer_user_uuid UUID NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('edit','approve','reject')),
    field_name TEXT,
    previous_value TEXT,
    new_value TEXT,
    rejection_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_review_logs_document_uuid ON review_logs(document_uuid);
CREATE INDEX idx_review_logs_extraction_uuid ON review_logs(extraction_uuid);
```

### `audit_events`

Stores append-only lifecycle events.

```sql
CREATE TABLE audit_events (
    id BIGSERIAL PRIMARY KEY,
    audit_event_uuid UUID NOT NULL UNIQUE,
    document_uuid UUID REFERENCES documents(document_uuid),
    extraction_uuid UUID REFERENCES extraction_runs(extraction_uuid),
    actor_user_uuid UUID,
    request_uuid UUID,
    event_type TEXT NOT NULL,
    event_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_events_document_uuid ON audit_events(document_uuid);
CREATE INDEX idx_audit_events_extraction_uuid ON audit_events(extraction_uuid);
CREATE INDEX idx_audit_events_event_type ON audit_events(event_type);
CREATE INDEX idx_audit_events_created_at ON audit_events(created_at);
```

## 9. Audit Trail and UUID Search

Required audit event types:

```text
document.uploaded
document.queued
document.preprocessing_started
document.extraction_started
document.extraction_completed
document.validation_started
document.validation_failed
document.retry_started
document.retry_completed
document.extracted
document.review_started
review.field_edited
review.approved
review.rejected
document.persisted
document.failed
```

UUID search must support:

1. Search by `document_uuid`.
2. Search by `extraction_uuid`.
3. Current status lookup.
4. Full lifecycle trace.
5. Raw extracted payload lookup.
6. Reviewed payload lookup.
7. Reviewer edit history.
8. Diff between extracted and reviewed values.

Diff response shape:

```json
{
  "document_uuid": "00000000-0000-0000-0000-000000000000",
  "extraction_uuid": "11111111-1111-1111-1111-111111111111",
  "fields": [
    {
      "field": "full_name",
      "extracted_value": "JOHN A DOE",
      "reviewed_value": "JOHN DOE",
      "changed": true,
      "changed_by_user_uuid": "22222222-2222-2222-2222-222222222222",
      "changed_at": "2026-04-21T10:00:00Z"
    }
  ]
}
```

## 10. Validation and Retry Logic

Validation fails when:

1. Response is not valid JSON.
2. Response is not an object.
3. Required fields are missing.
4. Extra fields are present.
5. Any non-null value is not a string.
6. Any field exceeds configured length limits.
7. The payload cannot be parsed into the Pydantic model.

Canonicalization:

1. Replace non-breaking spaces with normal spaces.
2. Trim whitespace.
3. Convert empty strings to `null`.
4. Preserve visible text casing unless the reviewer changes it.
5. Do not infer missing values.

Retry policy:

```text
max_attempts = 2
initial_attempt = 1
retry_attempt = 2
```

Retry conditions:

1. Schema validation failure.
2. Invalid JSON.
3. Additional fields returned.
4. Required fields missing.
5. Field type mismatch.
6. LLM response parsing failure.

Retry prompt:

```text
You are re-running extraction because the previous output failed validation.

Return exactly the required JSON schema.
Use null for any missing, unclear, uncertain, or unsupported value.
Do not include explanations.
Do not include markdown.
Do not include extra keys.
All keys must be present.
All non-null values must be strings.
Keep values literal and compact.
Do not hallucinate.
```

If validation fails after retry:

1. If the payload is parseable but invalid, route to manual review with validation errors visible.
2. If no parseable structured payload exists, mark extraction run `failed`.

## 11. API Design: FastAPI

### `POST /documents/upload`

Uploads a document and starts asynchronous extraction.

Response:

```json
{
  "document_uuid": "00000000-0000-0000-0000-000000000000",
  "extraction_uuid": "11111111-1111-1111-1111-111111111111",
  "status": "queued"
}
```

### `GET /documents/{uuid}/status`

Returns document and latest extraction status.

```json
{
  "document_uuid": "00000000-0000-0000-0000-000000000000",
  "status": "in_review",
  "latest_extraction": {
    "extraction_uuid": "11111111-1111-1111-1111-111111111111",
    "status": "extracted",
    "attempts": 1,
    "validation_errors": []
  }
}
```

### `GET /documents/{uuid}/extraction`

Returns extracted and reviewed data for UI display.

```json
{
  "document_uuid": "00000000-0000-0000-0000-000000000000",
  "extraction_uuid": "11111111-1111-1111-1111-111111111111",
  "status": "in_review",
  "schema_version": "identity_document.v1",
  "fields": [
    {
      "field": "full_name",
      "extracted_value": "JOHN DOE",
      "reviewed_value": null,
      "editable": true,
      "validation_status": "valid"
    }
  ]
}
```

### `POST /documents/{uuid}/review`

Submits reviewer edits, approval, or rejection.

Approve request:

```json
{
  "action": "approve",
  "extraction_uuid": "11111111-1111-1111-1111-111111111111",
  "reviewed_payload": {
    "document_type": "national_id",
    "full_name": "JOHN DOE",
    "first_name": "JOHN",
    "last_name": "DOE",
    "id_number": "123456789",
    "document_number": null,
    "date_of_birth": "1990-01-01",
    "sex": "M",
    "gender": "Male",
    "nationality": "USA",
    "place_of_birth": null,
    "issue_date": null,
    "expiry_date": null,
    "issuing_authority": null,
    "address": null,
    "raw_full_text": "..."
  }
}
```

Reject request:

```json
{
  "action": "reject",
  "extraction_uuid": "11111111-1111-1111-1111-111111111111",
  "rejection_reason": "Document image is unreadable"
}
```

### `GET /audit/{uuid}`

Returns audit events for either document UUID or extraction UUID.

```json
{
  "uuid": "00000000-0000-0000-0000-000000000000",
  "events": [
    {
      "audit_event_uuid": "33333333-3333-3333-3333-333333333333",
      "event_type": "document.uploaded",
      "actor_user_uuid": "44444444-4444-4444-4444-444444444444",
      "event_payload": {
        "original_filename": "id-card.jpg",
        "content_type": "image/jpeg"
      },
      "created_at": "2026-04-21T10:00:00Z"
    }
  ]
}
```

## 12. Non-Functional Requirements

### Scalability

1. Extraction runs asynchronously outside the upload request.
2. Workers scale horizontally by queue depth.
3. OpenAI rate limits are enforced centrally in the LLM Adapter.
4. Large PDFs are split into page-level or document-level extraction jobs according to policy.

### Reliability

1. Upload and extraction commands are idempotent where possible.
2. Worker crashes do not lose document state.
3. LangGraph state uses a durable checkpointer in production.
4. Status transitions and audit writes are transactional where practical.

### Traceability

1. Store model name, prompt version, schema version, extraction UUID, retry count, and validation errors.
2. Store raw LLM response separately from normalized payload.
3. Every production record links back to `document_uuid` and `extraction_uuid`.

### Auditability

1. Audit events are append-only.
2. Reviewer edits preserve previous and new values.
3. Rejected documents remain traceable.

### Observability

Required metrics:

1. Queue depth.
2. Processing duration by stage.
3. LLM request latency.
4. LLM timeout count.
5. Validation failure count.
6. Retry count.
7. Extraction failure count.
8. Manual review backlog.
9. Persist success and failure count.

### Security

1. Authenticate all APIs.
2. Authorize by user, tenant, role, and document ownership.
3. Encrypt object storage and database storage at rest.
4. Use signed URLs for controlled artifact access.
5. Redact sensitive field values in logs.
6. Store OpenAI credentials in a secret manager.
7. Apply file size, file type, and page count limits.
8. Run malware scanning before extraction where required.

## 13. Implementation Notes

1. Version prompt templates independently from code.
2. Version JSON schemas independently from prompts.
3. Store raw LLM output before canonicalization.
4. Log all retry attempts with validation errors.
5. Separate machine-extracted staging data from reviewer-approved production data.
6. Use UUID-based object storage paths.
7. Keep the LLM adapter behind an internal interface so GPT-4o and GPT-4o-mini can be selected by policy.
8. Treat `raw_full_text` as an LLM-generated visible-text transcription, not as Tesseract or traditional OCR output.
9. Do not persist unreviewed extraction data as authoritative banking data.
10. Keep prompt templates, schema definitions, preprocessing defaults, and model selection in versioned configuration.

Recommended preprocessing defaults:

```json
{
  "max_side_for_upload": 1600,
  "jpeg_quality": 90,
  "image_mode": "RGB",
  "output_format": "JPEG"
}
```

Recommended model configuration:

```json
{
  "primary_model": "gpt-4o",
  "fallback_model": "gpt-4o-mini",
  "capability": "vision_structured_json_extraction",
  "strict_schema": true
}
```

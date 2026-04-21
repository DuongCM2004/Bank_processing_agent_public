# Database Schema And Migration Plan

This document is the implementation-oriented database plan for the banking Document Processing Agent. It is aligned to the current migrations in [db/migrations](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/db/migrations) and fills the remaining MVP gaps around LLM extraction, manual review, evidence linking, audit, and identity.

## Current Documents Module Baseline

Use [production-llm-document-extraction-backend-spec.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\production-llm-document-extraction-backend-spec.md) as the current migration source for document extraction. Required production tables are `documents`, `extraction_runs`, `extracted_data`, `review_logs`, and `audit_events`, with UUID indexes, lifecycle status fields, raw-vs-reviewed payload separation, and approved-only persistence. Dataset, training, benchmark, and model-evaluation tables are not part of the current Documents extraction migration scope.

## 1. Relational Schema For Core Entities

Use PostgreSQL with logical schemas:

- `ops_core`
  cases, documents, pages, workflow runs, outbox
- `ops_ai`
  artifacts, OCR, classification, extraction, evidence refs
- `ops_rules`
  validation, compliance, risk, decisions
- `ops_review`
  review tasks, review actions, review evidence refs
- `ops_audit`
  immutable audit events
- `ops_identity`
  users and roles

This schema supports:

- traceable case lifecycle
- async workflow status
- machine result versioning
- evidence linkage
- append-only review and audit trails

## 2. Blob / Document Storage Mapping Assumptions

### Object storage is authoritative for large blobs

Store in S3 / MinIO:

- raw uploaded documents
- page render images
- OCR block JSON
- layout JSON
- extraction bundle JSON
- prompt payloads and responses
- review bundle exports

### Relational storage is authoritative for metadata and state

Store in PostgreSQL:

- case state
- document metadata
- page metadata
- workflow state
- artifact registry
- OCR/classification/extraction summary rows
- validation/compliance/risk/decision rows
- review actions
- audit events

### Mapping rule

Every blob object must map back to a row in `ops_ai.artifacts` with:

- immutable `object_key`
- `content_hash`
- `producer_service`
- `producer_version`
- `case_id`
- `document_id` and `document_version_id` where applicable

## 3. Key Tables

### Core workflow tables

- `ops_core.cases`
- `ops_core.case_status_history`
- `ops_core.documents`
- `ops_core.document_versions`
- `ops_core.document_pages`
- `ops_core.workflow_runs`
- `ops_core.workflow_step_runs`
- `ops_core.outbox_events`

### AI processing tables

- `ops_ai.artifacts`
- `ops_ai.ocr_runs`
- `ops_ai.ocr_page_results`
- `ops_ai.classification_runs`
- `ops_ai.extraction_runs`
- `ops_ai.extracted_fields`
- `ops_ai.field_evidence_refs`

### Rules / findings tables

- `ops_rules.validation_runs`
- `ops_rules.validation_results`
- `ops_rules.validation_evidence_refs`
- `ops_rules.compliance_evaluations`
- `ops_rules.compliance_control_results`
- `ops_rules.risk_findings`
- `ops_rules.decision_runs`
- `ops_rules.decision_inputs`

### Review and audit tables

- `ops_review.review_tasks`
- `ops_review.review_actions`
- `ops_review.review_action_evidence_refs`
- `ops_audit.audit_events`

### Identity tables

- `ops_identity.users`
- `ops_identity.roles`
- `ops_identity.user_role_assignments`

## 4. Key Fields

### `ops_core.cases`

- `case_id`
- `workflow_type`
- `priority`
- `status`
- `compliance_status`
- `assigned_queue`
- `review_required`
- `final_outcome`
- `current_workflow_run_id`
- `created_by`
- `record_version`
- `created_at_utc`
- `updated_at_utc`

### `ops_core.documents`

- `document_id`
- `case_id`
- `document_role`
- `filename`
- `mime_type`
- `source_channel`
- `retention_class`
- `status`
- `latest_document_version_id`

### `ops_core.document_versions`

- `document_version_id`
- `document_id`
- `version_no`
- `raw_object_key`
- `sha256`
- `byte_size`
- `page_count`
- `quarantine_status`
- `supersedes_document_version_id`

### `ops_core.document_pages`

- `document_page_id`
- `document_id`
- `document_version_id`
- `page_number`
- `width_px`
- `height_px`
- `rotation_degrees`
- `preview_artifact_id`

### `ops_ai.ocr_runs`

- `ocr_run_id`
- `case_id`
- `document_id`
- `document_version_id`
- `source_artifact_id`
- `output_artifact_id`
- `model_version`
- `preprocess_profile_version`
- `status`
- `overall_confidence`

### `ops_ai.extracted_fields`

- `extracted_field_id`
- `extraction_run_id`
- `field_name`
- `field_value`
- `normalized_value`
- `value_type`
- `required_flag`
- `confidence_score`
- `confidence_label`
- `method`
- `status`
- `reason_code`
- `reviewed_by_human`

### `ops_rules.validation_results`

- `validation_result_id`
- `validation_run_id`
- `rule_id`
- `rule_version`
- `severity`
- `result`
- `reason_code`
- `impacted_field_name`
- `details_json`

### `ops_rules.compliance_control_results`

- `compliance_control_result_id`
- `compliance_evaluation_id`
- `control_id`
- `control_version`
- `status`
- `severity`
- `reason_code`
- `external_ref`
- `details_json`

### `ops_rules.risk_findings`

- `risk_finding_id`
- `finding_type`
- `severity`
- `reason_code`
- `status`
- `summary`
- `evidence_json`

### `ops_rules.decision_runs`

- `decision_run_id`
- `case_id`
- `workflow_run_id`
- `decision_type`
- `route`
- `decision_status`
- `decision_confidence`
- `rationale_json`
- `requires_human_review`
- `rule_pack_version`
- `prompt_version`
- `model_version`

### `ops_review.review_actions`

- `review_action_id`
- `case_id`
- `review_task_id`
- `action_type`
- `actor_id`
- `reason_code`
- `comment`
- `payload_json`
- `trace_id`

### `ops_audit.audit_events`

- `event_id`
- `case_id`
- `resource_type`
- `resource_id`
- `action`
- `actor_type`
- `actor_id`
- `trace_id`
- `details_json`
- `immutable_hash`

## 5. Foreign Keys And Relationships

Primary relationships:

1. `cases -> documents`
2. `documents -> document_versions`
3. `document_versions -> document_pages`
4. `cases -> workflow_runs`
5. `workflow_runs -> workflow_step_runs`
6. `cases -> review_tasks`
7. `review_tasks -> review_actions`
8. `cases -> audit_events`
9. `documents/document_versions -> artifacts`
10. `ocr_runs/classification_runs/extraction_runs -> documents`
11. `extracted_fields -> field_evidence_refs`
12. `validation_results -> validation_evidence_refs`
13. `review_actions -> review_action_evidence_refs`
14. `cases -> compliance_evaluations -> compliance_control_results`
15. `cases -> risk_findings`
16. `cases -> decision_runs -> decision_inputs`
17. `users -> user_role_assignments -> roles`

Traceability chain:

`case -> document -> document_version -> document_page -> artifact -> run -> evidence ref -> review/audit`

## 6. Indexing Recommendations

Keep indexes focused on operational queries:

### Queue and workflow

- `ops_core.cases (workflow_type, status)`
- `ops_core.cases (assigned_queue, priority, updated_at_utc desc)`
- `ops_core.workflow_runs (case_id)`
- `ops_core.workflow_step_runs (case_id, step_name, status)`

### Document and evidence lookup

- `ops_core.documents (case_id)`
- `ops_core.document_pages (document_id, page_number)`
- `ops_ai.artifacts (document_version_id, artifact_type, created_at_utc desc)`
- `ops_ai.field_evidence_refs (extracted_field_id, evidence_rank)`

### Findings and review

- `ops_rules.validation_results (case_id, severity, created_at_utc desc)`
- `ops_rules.compliance_control_results (case_id, control_id, created_at_utc desc)`
- `ops_rules.risk_findings (case_id, severity, created_at_utc desc)`
- `ops_review.review_tasks (status, assigned_queue, priority, created_at_utc)`
- `ops_review.review_actions (case_id, created_at_utc desc)`

### Audit

- `ops_audit.audit_events (case_id, occurred_at_utc desc)`
- `ops_audit.audit_events (trace_id)`
- `ops_audit.audit_events (resource_type, resource_id, occurred_at_utc desc)` in a later migration if query volume needs it

## 7. Versioning Strategy

Versioning must be append-only for evidence-bearing outputs.

### Immutable versioned records

- `document_versions`
- `ocr_runs`
- `classification_runs`
- `extraction_runs`
- `validation_runs`
- `compliance_evaluations`
- `decision_runs`
- `review_actions`
- `audit_events`

### Version reference fields to persist where relevant

- `workflow_definition_version`
- `schema_version`
- `rule_pack_version`
- `ocr_model_version` or `model_version`
- `classifier_model_version`
- `prompt_version`
- `preprocess_profile_version`

### No in-place overwrite rule

Do not update a prior machine result row to “correct” history. Create a new run row or a human review action row and link it by evidence.

## 8. Migration Sequence For MVP

Recommended release sequence:

1. Create logical schemas.
2. Create core case/document/workflow/outbox tables.
3. Create artifact/extraction/validation/decision/review/audit tables.
4. Add identity and document page tables.
5. Add OCR/classification/compliance/risk/evidence-link tables.
6. Seed roles and reference values.
7. Implement repository layer against this schema.

Current migration files:

1. [0001_init_schemas.sql](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/db/migrations/0001_init_schemas.sql)
2. [0002_core_tables.sql](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/db/migrations/0002_core_tables.sql)
3. [0003_ai_rules_review_audit_tables.sql](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/db/migrations/0003_ai_rules_review_audit_tables.sql)
4. [0004_document_pages_identity.sql](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/db/migrations/0004_document_pages_identity.sql)
5. [0005_ai_evidence_compliance.sql](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/db/migrations/0005_ai_evidence_compliance.sql)

## 9. Example Migration Files Or Pseudo-Migrations

Already added as SQL examples:

- schema bootstrap
- core entities
- review and audit foundation
- identity and document page support
- OCR, classification, compliance, risk, and evidence-link extensions

Practical migration rule:

- additive first
- backfill second
- constraint tightening third

Example future migration pattern:

```sql
BEGIN;

ALTER TABLE ops_rules.decision_runs
ADD COLUMN closure_reason_code TEXT NULL;

UPDATE ops_rules.decision_runs
SET closure_reason_code = 'legacy_backfill'
WHERE decision_type = 'closure_recommendation'
  AND closure_reason_code IS NULL;

COMMIT;
```

## 10. Data Retention / Audit Considerations At Schema Level

Retention-sensitive fields already exist or should exist:

- `retention_class` on documents
- immutable `audit_events`
- immutable `document_versions`
- immutable machine result runs

Schema-level retention guidance:

1. Never hard-delete audit events in normal operations.
2. Never hard-delete review actions tied to closed or regulated cases.
3. Retain document version rows even if blobs move to cold storage.
4. Use object storage lifecycle policies for blobs, but preserve artifact metadata rows.
5. Add `legal_hold` tables later before production if regulatory retention varies by jurisdiction or case type.

Recommended later extensions:

- `ops_core.legal_holds`
- table partitioning for `audit_events`, `workflow_step_runs`, `review_actions`
- signed hash chaining on audit rows for stronger tamper evidence

## MVP-First Rationale

This schema is intentionally conservative:

- enough normalization for traceability
- enough append-only history for audit and replay
- enough workflow metadata for async processing and retries
- enough evidence linking for reviewer trust and compliance review

It avoids premature complexity by keeping large artifacts in object storage and using PostgreSQL for durable operational truth.

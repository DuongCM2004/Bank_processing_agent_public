# Database and Persistence Schema Design for Ops Agent

## Role

Backend Engineer and Data Architect for a banking-grade Document Processing Agent.

## Objective

Design how the system stores cases, documents, OCR results, extracted fields, validations, decisions, audit logs, and review actions in a way that preserves evidence traceability, supports auditability, and is practical for implementation.

## Assumptions

1. PostgreSQL is the transactional system of record for metadata, workflow state, review actions, and audit history.
2. S3 / MinIO is the system of record for raw documents and large derived artifacts such as page renders, OCR JSON, layout JSON, prompt/response payloads, and review bundles.
3. OpenSearch remains a rebuildable read model, not a source of truth.
4. The current explicit case state machine in the repo must be preserved.
5. Schema design must support asynchronous workflows, retries, and replay without losing lineage.

## Deliverables

- Core entities
- Relationships
- Case lifecycle representation
- Document metadata model
- Extraction result model
- Validation result model
- Decision model
- Audit log model
- Human review action model
- Versioning considerations
- MVP schema
- Scale-stage schema extensions

## Dependencies

1. [ops-agent-prd.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ops-agent-prd.md)
2. [solution-architecture-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\solution-architecture-blueprint.md)
3. [backend-engineering-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\backend-engineering-blueprint.md)
4. [data-engineering-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\data-engineering-blueprint.md)
5. [ai-architecture.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ai-architecture.md)
6. [compliance-risk-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\compliance-risk-controls.md)

## Risks

1. Workflow state and audit history drift apart.
2. Large AI artifacts are pushed into relational tables and make transactional paths too heavy.
3. Reviewer corrections overwrite machine history instead of creating versioned records.
4. Async retries create duplicate runs or duplicate side effects.
5. OpenSearch projections are mistaken for the canonical source of operational truth.

## MVP vs Scale notes

### MVP

1. Keep the persistence design simple:
   PostgreSQL + S3 / MinIO + OpenSearch projection.
2. Use append-only run tables and status-history tables instead of trying to compress everything into one current-state row.
3. Store detailed OCR/layout/prompt payloads in object storage, not in PostgreSQL rows.

### Scale

1. Add partitioning, archival, legal-hold controls, and cross-region replication.
2. Add richer external-handoff, entity-linking, and analytical-support tables only after core workflow stability.
3. Add dataset and annotation schema extensions without changing the operational source-of-truth model.

## 1. Storage Boundary Rules

### 1.1 What belongs in relational storage

Store in PostgreSQL:

1. case and workflow state
2. document metadata
3. artifact registry metadata
4. extracted field rows
5. validation results
6. compliance control results
7. decision results
8. review tasks and review actions
9. audit events
10. workflow runs, step runs, and outbox events
11. version references for rules, prompts, models, and schemas

### 1.2 What belongs in blob / object storage

Store in S3 / MinIO:

1. raw uploaded files
2. rendered page images
3. OCR block JSON
4. layout JSON
5. extraction bundle JSON
6. prompt / response payloads
7. review bundles
8. audit exports and benchmark exports

### 1.3 Design rule

Every large or nested artifact stored in object storage must have:

1. an immutable object key,
2. a content hash,
3. a producing service,
4. a producing version reference,
5. a registry row in PostgreSQL.

## 2. PostgreSQL Logical Schemas

Use these PostgreSQL schemas:

1. `ops_core`
   cases, documents, workflow runs, outbox
2. `ops_ai`
   artifacts, OCR runs, classification runs, extraction runs, extracted fields
3. `ops_rules`
   validation runs, validation results, compliance control results, decision runs
4. `ops_review`
   review tasks, review actions
5. `ops_audit`
   audit events, status history, lineage support

## 3. Core Entities

### 3.1 `ops_core.cases`

Represents one banking workflow case.

| Column | Type | Constraints / notes |
|---|---|---|
| `case_id` | text | PK |
| `workflow_type` | text | not null |
| `priority` | text | not null |
| `customer_reference` | text | nullable |
| `status` | text | current operational status |
| `compliance_status` | text | current compliance status |
| `assigned_queue` | text | current queue |
| `review_required` | boolean | default false |
| `final_outcome` | text | nullable |
| `current_workflow_run_id` | text | nullable FK to workflow run |
| `created_by` | text | actor or source system |
| `created_at_utc` | timestamptz | not null |
| `updated_at_utc` | timestamptz | not null |
| `record_version` | bigint | optimistic locking / monotonic update version |

Indexes:

1. `(workflow_type, status)`
2. `(assigned_queue, priority, updated_at_utc desc)`
3. `(customer_reference)`

### 3.2 `ops_core.case_status_history`

Append-only status history for workflow reconstruction.

| Column | Type | Constraints / notes |
|---|---|---|
| `case_status_event_id` | text | PK |
| `case_id` | text | FK |
| `from_status` | text | nullable for initial event |
| `to_status` | text | not null |
| `reason_code` | text | not null |
| `actor_type` | text | system / user / service |
| `actor_id` | text | not null |
| `trace_id` | text | not null |
| `occurred_at_utc` | timestamptz | not null |

### 3.3 `ops_core.documents`

Logical document registered to a case.

| Column | Type | Constraints / notes |
|---|---|---|
| `document_id` | text | PK |
| `case_id` | text | FK |
| `document_role` | text | id_document / proof_of_address / bank_statement / supporting_form etc. |
| `filename` | text | not null |
| `mime_type` | text | not null |
| `source_channel` | text | not null |
| `retention_class` | text | not null |
| `status` | text | current processing status |
| `latest_document_version_id` | text | current active version |
| `created_at_utc` | timestamptz | not null |
| `updated_at_utc` | timestamptz | not null |

Indexes:

1. `(case_id)`
2. `(case_id, document_role)`

### 3.4 `ops_core.document_versions`

Immutable physical-version record for each document upload or resubmission.

| Column | Type | Constraints / notes |
|---|---|---|
| `document_version_id` | text | PK |
| `document_id` | text | FK |
| `version_no` | integer | unique per document |
| `raw_object_key` | text | not null |
| `sha256` | text | not null |
| `byte_size` | bigint | nullable |
| `page_count` | integer | nullable |
| `quarantine_status` | text | accepted / quarantined / rejected |
| `supersedes_document_version_id` | text | nullable self-reference |
| `created_by` | text | actor or source |
| `created_at_utc` | timestamptz | not null |

Constraints:

1. unique `(document_id, version_no)`
2. unique `(sha256, document_id, version_no)` optional depending on dedupe policy

### 3.5 `ops_core.workflow_runs`

One parent workflow execution per case attempt.

| Column | Type | Constraints / notes |
|---|---|---|
| `workflow_run_id` | text | PK |
| `case_id` | text | FK |
| `workflow_engine` | text | default `temporal` |
| `workflow_definition_version` | text | not null |
| `status` | text | queued / running / waiting_review / completed / failed / cancelled |
| `started_at_utc` | timestamptz | not null |
| `finished_at_utc` | timestamptz | nullable |
| `trace_id` | text | not null |

### 3.6 `ops_core.workflow_step_runs`

Tracks step-level async execution and retry behavior.

| Column | Type | Constraints / notes |
|---|---|---|
| `workflow_step_run_id` | text | PK |
| `workflow_run_id` | text | FK |
| `case_id` | text | FK |
| `document_id` | text | nullable FK |
| `step_name` | text | ocr / layout / extraction / validation / compliance / decision |
| `step_version` | text | not null |
| `attempt_no` | integer | not null |
| `status` | text | queued / running / completed / failed / dead_lettered |
| `input_artifact_id` | text | nullable |
| `output_artifact_id` | text | nullable |
| `error_code` | text | nullable |
| `error_message` | text | nullable |
| `started_at_utc` | timestamptz | nullable |
| `finished_at_utc` | timestamptz | nullable |
| `trace_id` | text | not null |

Constraints:

1. unique `(workflow_run_id, document_id, step_name, step_version, attempt_no)`

### 3.7 `ops_core.outbox_events`

Transactional outbox for event emission.

| Column | Type | Constraints / notes |
|---|---|---|
| `outbox_event_id` | text | PK |
| `aggregate_type` | text | case / document / review_task / decision |
| `aggregate_id` | text | not null |
| `event_type` | text | not null |
| `payload_json` | jsonb | not null |
| `publish_status` | text | pending / published / failed |
| `created_at_utc` | timestamptz | not null |
| `published_at_utc` | timestamptz | nullable |
| `trace_id` | text | not null |

## 4. Relationships Between Entities

### 4.1 Primary relationships

1. one `case` has many `documents`
2. one `document` has many `document_versions`
3. one `case` has many `workflow_runs`
4. one `workflow_run` has many `workflow_step_runs`
5. one `case` has many `review_tasks`
6. one `case` has many `audit_events`
7. one `document_version` has many AI artifacts
8. one `document` has many classification, extraction, and validation runs over time
9. one `case` has many decision runs over time

### 4.2 Traceability rule

Every critical output row must be traceable back through:

`case -> document -> document_version -> artifact -> run -> evidence ref`

## 5. Case Lifecycle Representation

### 5.1 Current-state representation

Use `ops_core.cases.status` as the canonical current state for operational APIs.

### 5.2 Historical representation

Use:

1. `ops_core.case_status_history` for state changes
2. `ops_core.workflow_runs` for workflow-level attempts
3. `ops_core.workflow_step_runs` for async step progress

### 5.3 Why both are needed

1. current state supports fast UI and API retrieval
2. history supports audit reconstruction
3. workflow step runs support retry analysis and async troubleshooting

## 6. Document Metadata Model

### 6.1 Metadata tables

Use:

1. `ops_core.documents`
2. `ops_core.document_versions`
3. `ops_ai.artifacts`

### 6.2 `ops_ai.artifacts`

Generic artifact registry for raw and derived artifacts.

| Column | Type | Constraints / notes |
|---|---|---|
| `artifact_id` | text | PK |
| `case_id` | text | FK |
| `document_id` | text | nullable FK |
| `document_version_id` | text | nullable FK |
| `artifact_type` | text | raw_upload / page_render / ocr_json / layout_json / extraction_json / prompt_response / review_bundle |
| `object_key` | text | not null |
| `content_hash` | text | not null |
| `producer_service` | text | not null |
| `producer_version` | text | not null |
| `created_at_utc` | timestamptz | not null |

Indexes:

1. `(document_version_id, artifact_type, created_at_utc desc)`
2. `(case_id, artifact_type)`

### 6.3 Evidence-linking rule

All downstream evidence references must resolve either to:

1. a document version plus page and bounding box, or
2. an artifact registry row plus structured locator within the artifact.

## 7. Extraction Result Model

### 7.1 `ops_ai.extraction_runs`

One run per extraction attempt for one document version and schema version.

| Column | Type | Constraints / notes |
|---|---|---|
| `extraction_run_id` | text | PK |
| `case_id` | text | FK |
| `document_id` | text | FK |
| `document_version_id` | text | FK |
| `schema_version` | text | not null |
| `classifier_result_id` | text | nullable FK |
| `ocr_result_id` | text | nullable FK |
| `layout_artifact_id` | text | nullable FK |
| `method` | text | rule_anchor / template / llm_reconcile / mixed |
| `prompt_version` | text | nullable |
| `model_version` | text | nullable |
| `status` | text | completed / needs_review / insufficient_evidence / error |
| `extraction_confidence` | numeric(5,4) | nullable |
| `created_at_utc` | timestamptz | not null |

### 7.2 `ops_ai.extracted_fields`

One row per field result version.

| Column | Type | Constraints / notes |
|---|---|---|
| `extracted_field_id` | text | PK |
| `extraction_run_id` | text | FK |
| `case_id` | text | FK |
| `document_id` | text | FK |
| `document_version_id` | text | FK |
| `field_name` | text | not null |
| `field_value` | text | nullable |
| `normalized_value` | text | nullable |
| `value_type` | text | string / date / decimal / enum |
| `required_flag` | boolean | not null |
| `confidence_score` | numeric(5,4) | nullable |
| `confidence_label` | text | nullable |
| `method` | text | not null |
| `status` | text | extracted / missing / conflict / corrected |
| `reason_code` | text | nullable |
| `reviewed_by_human` | boolean | default false |
| `created_at_utc` | timestamptz | not null |

Indexes:

1. `(case_id, field_name, created_at_utc desc)`
2. `(document_id, field_name, created_at_utc desc)`

### 7.3 `ops_ai.field_evidence_refs`

Normalized evidence refs for field-level traceability.

| Column | Type | Constraints / notes |
|---|---|---|
| `field_evidence_ref_id` | text | PK |
| `extracted_field_id` | text | FK |
| `document_id` | text | FK |
| `document_version_id` | text | FK |
| `artifact_id` | text | nullable FK |
| `page_number` | integer | nullable |
| `text_span` | text | nullable |
| `bbox_json` | jsonb | nullable |
| `evidence_rank` | integer | default 1 |
| `created_at_utc` | timestamptz | not null |

Design rule:

critical extracted fields must have at least one evidence ref row.

## 8. Validation Result Model

### 8.1 `ops_rules.validation_runs`

| Column | Type | Constraints / notes |
|---|---|---|
| `validation_run_id` | text | PK |
| `case_id` | text | FK |
| `document_id` | text | nullable FK |
| `document_version_id` | text | nullable FK |
| `rule_pack_version` | text | not null |
| `schema_version` | text | nullable |
| `status` | text | completed / failed / needs_review |
| `validation_confidence` | numeric(5,4) | nullable |
| `created_at_utc` | timestamptz | not null |

### 8.2 `ops_rules.validation_results`

One row per rule result.

| Column | Type | Constraints / notes |
|---|---|---|
| `validation_result_id` | text | PK |
| `validation_run_id` | text | FK |
| `case_id` | text | FK |
| `document_id` | text | nullable FK |
| `rule_id` | text | not null |
| `rule_version` | text | not null |
| `severity` | text | info / warning / high / critical |
| `result` | text | pass / fail / warn / review_required |
| `reason_code` | text | not null |
| `impacted_field_name` | text | nullable |
| `details_json` | jsonb | nullable |
| `created_at_utc` | timestamptz | not null |

### 8.3 `ops_rules.validation_evidence_refs`

Optional join table for rule-to-evidence linkage.

| Column | Type | Constraints / notes |
|---|---|---|
| `validation_evidence_ref_id` | text | PK |
| `validation_result_id` | text | FK |
| `artifact_id` | text | nullable FK |
| `document_id` | text | nullable FK |
| `page_number` | integer | nullable |
| `text_span` | text | nullable |
| `bbox_json` | jsonb | nullable |

## 9. Decision Model

### 9.1 `ops_rules.decision_runs`

Each evaluation of next route or final recommendation gets its own run row.

| Column | Type | Constraints / notes |
|---|---|---|
| `decision_run_id` | text | PK |
| `case_id` | text | FK |
| `workflow_run_id` | text | FK |
| `decision_type` | text | route_evaluation / closure_recommendation |
| `route` | text | auto_process / cross_check / human_review / specialist_escalation |
| `decision_status` | text | completed / blocked / needs_review |
| `decision_confidence` | numeric(5,4) | nullable |
| `rationale_json` | jsonb | nullable |
| `requires_human_review` | boolean | not null |
| `rule_pack_version` | text | not null |
| `prompt_version` | text | nullable |
| `model_version` | text | nullable |
| `created_at_utc` | timestamptz | not null |

### 9.2 `ops_rules.decision_inputs`

Optional snapshot table for audit / replay of key aggregated inputs.

| Column | Type | Constraints / notes |
|---|---|---|
| `decision_input_id` | text | PK |
| `decision_run_id` | text | FK |
| `ocr_confidence` | numeric(5,4) | nullable |
| `classification_confidence` | numeric(5,4) | nullable |
| `extraction_confidence` | numeric(5,4) | nullable |
| `validation_confidence` | numeric(5,4) | nullable |
| `compliance_status` | text | not null |
| `critical_failures_json` | jsonb | default `[]` |
| `pending_critical_checks_json` | jsonb | default `[]` |

## 10. Audit Log Model

### 10.1 `ops_audit.audit_events`

Immutable audit event store.

| Column | Type | Constraints / notes |
|---|---|---|
| `event_id` | text | PK |
| `case_id` | text | FK |
| `resource_type` | text | case / document / review_task / decision / workflow_run |
| `resource_id` | text | not null |
| `action` | text | not null |
| `actor_type` | text | system / user / service |
| `actor_id` | text | not null |
| `trace_id` | text | not null |
| `occurred_at_utc` | timestamptz | not null |
| `details_json` | jsonb | default `{}` |
| `immutable_hash` | text | nullable in MVP, recommended before production |

Indexes:

1. `(case_id, occurred_at_utc)`
2. `(resource_type, resource_id, occurred_at_utc)`
3. `(trace_id)`

### 10.2 Audit rule

Every mutating workflow action must write:

1. the domain row(s),
2. the corresponding audit event,
3. the outbox event where needed,

inside the same transaction when practical.

## 11. Human Review Action Model

### 11.1 `ops_review.review_tasks`

| Column | Type | Constraints / notes |
|---|---|---|
| `review_task_id` | text | PK |
| `case_id` | text | FK |
| `task_type` | text | ops_review / compliance_review / fraud_review |
| `status` | text | open / claimed / completed / cancelled |
| `assigned_queue` | text | not null |
| `assigned_to` | text | nullable |
| `priority` | text | denormalized for queue sort |
| `reason_codes_json` | jsonb | not null |
| `created_at_utc` | timestamptz | not null |
| `updated_at_utc` | timestamptz | not null |
| `claimed_at_utc` | timestamptz | nullable |
| `completed_at_utc` | timestamptz | nullable |

Indexes:

1. `(status, assigned_queue, priority, created_at_utc)`
2. `(assigned_to, status)`

### 11.2 `ops_review.review_actions`

Append-only manual actions taken on a case.

| Column | Type | Constraints / notes |
|---|---|---|
| `review_action_id` | text | PK |
| `case_id` | text | FK |
| `review_task_id` | text | nullable FK |
| `action_type` | text | claim / correct_field / escalate / revalidate / close / comment |
| `actor_id` | text | not null |
| `reason_code` | text | not null |
| `comment` | text | nullable |
| `payload_json` | jsonb | not null |
| `created_at_utc` | timestamptz | not null |
| `trace_id` | text | not null |

### 11.3 `ops_review.review_action_evidence_refs`

Evidence linkage for corrections and escalations.

| Column | Type | Constraints / notes |
|---|---|---|
| `review_action_evidence_ref_id` | text | PK |
| `review_action_id` | text | FK |
| `document_id` | text | FK |
| `document_version_id` | text | FK |
| `artifact_id` | text | nullable FK |
| `page_number` | integer | nullable |
| `text_span` | text | nullable |
| `bbox_json` | jsonb | nullable |

## 12. Versioning Considerations

### 12.1 No in-place overwrite rule

Do not overwrite:

1. raw documents,
2. document versions,
3. extraction runs,
4. validation runs,
5. decision runs,
6. review actions,
7. audit events.

Create a new row or version instead.

### 12.2 Version columns that must exist

Persist these version refs wherever relevant:

1. `workflow_definition_version`
2. `schema_version`
3. `rule_pack_version`
4. `ocr_model_version`
5. `classifier_model_version`
6. `prompt_version`
7. `preprocess_profile_version`

### 12.3 Replay rule

Any final recommendation or reviewer-visible machine output must be reproducible from:

1. the referenced source document version,
2. the referenced artifact registry rows,
3. the run row,
4. the version refs,
5. the evidence refs.

## 13. MVP Schema

### 13.1 Required MVP tables

1. `ops_core.cases`
2. `ops_core.case_status_history`
3. `ops_core.documents`
4. `ops_core.document_versions`
5. `ops_core.workflow_runs`
6. `ops_core.workflow_step_runs`
7. `ops_core.outbox_events`
8. `ops_ai.artifacts`
9. `ops_ai.extraction_runs`
10. `ops_ai.extracted_fields`
11. `ops_ai.field_evidence_refs`
12. `ops_rules.validation_runs`
13. `ops_rules.validation_results`
14. `ops_rules.decision_runs`
15. `ops_review.review_tasks`
16. `ops_review.review_actions`
17. `ops_audit.audit_events`

### 13.2 MVP simplifications

1. OCR blocks, layout blocks, and full prompt payloads stay in object storage with artifact registry rows, not decomposed relational tables.
2. `decision_inputs` and separate validation-evidence tables are optional in MVP if rationale and refs are captured in run payload JSON and artifacts.
3. OpenSearch projections are generated from these source tables but are not authoritative.

## 14. Scale-Stage Schema Extensions

### 14.1 Operational scale extensions

1. `ops_core.case_external_refs`
   for LOS, onboarding, and downstream-system correlation ids
2. `ops_core.legal_holds`
   for retention hold management
3. `ops_review.review_comments`
   if threaded review discussion becomes necessary
4. `ops_rules.compliance_control_results`
   fully normalized control-by-control status table

### 14.2 AI and analytics extensions

1. `ops_ai.ocr_runs`
   normalized OCR run summary table
2. `ops_ai.classification_runs`
   normalized classification run table
3. `ops_ai.prompt_invocations`
   structured prompt execution metadata
4. `ops_ml.datasets`, `ops_ml.dataset_items`, `ops_ml.annotations`
   for governed training and benchmark support
5. `ops_audit.lineage_edges`
   explicit lineage graph support

### 14.3 Scale-stage performance extensions

1. partition `audit_events`, `workflow_step_runs`, and `review_actions` by date
2. add partial indexes for active queues and open tasks
3. archive aged artifacts and aged closed-case projections while preserving retention rules

## 15. Recommended Persistence Stance

The persistence model for Ops Agent should remain:

1. relational for state, runs, decisions, review actions, and audit,
2. object-storage based for raw and large derived artifacts,
3. append-only for history and evidence,
4. versioned for all machine-produced outputs,
5. explicit enough that every reviewer action and every critical machine result can be traced back to source evidence.

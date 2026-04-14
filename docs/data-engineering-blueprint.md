# Data Engineering Blueprint for Ops Agent

## Role

Data Engineer for a banking-grade Document Processing Agent.

## Objective

Design the data pipelines, storage schemas, evidence traceability, annotation flows, and feedback loops required for both model training and operational workflows.

## Assumptions

1. Raw documents and derived artifacts must remain traceable end to end from ingestion through review, decision, and model retraining.
2. PostgreSQL remains the transactional system of record for metadata and workflow state.
3. S3 / MinIO remains the system of record for raw and derived document artifacts.
4. OpenSearch is read-optimized for operational search and audit lookup; it is not the system of record.
5. The same data platform must support both operations and ML development, but training datasets must be curated from governed source-of-truth records rather than ad hoc production exports.

## Deliverables

- Data architecture
- Schemas
- Pipelines
- Annotation flow
- Lineage
- Feedback loops

## Dependencies

1. [solution-architecture-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\solution-architecture-blueprint.md)
2. [ai-architecture.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ai-architecture.md)
3. [ml-engineering-plan.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ml-engineering-plan.md)
4. [compliance-risk-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\compliance-risk-controls.md)
5. [banking-document-rules.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\banking-document-rules.md)

## Risks

1. derived outputs become disconnected from source evidence
2. training data is built from stale or ungoverned exports
3. reviewer corrections are not normalized into reusable feedback
4. OpenSearch becomes mistaken for source of truth
5. schema drift across services breaks lineage and replay

## MVP vs Scale notes

### MVP

1. keep the storage design simple: PostgreSQL + S3 / MinIO + OpenSearch
2. use append-only event and artifact references rather than building a separate lakehouse immediately
3. create dataset-generation jobs from governed operational records
4. build annotation tooling support around a narrow set of document types

### Scale

1. add partitioned analytical storage or lakehouse patterns if data volume requires it
2. add richer dataset versioning, feature stores, and cross-region replication
3. expand lineage automation and data quality controls per domain

## 1. Data Architecture

## 1.1 Logical data zones

The platform should use five explicit data zones:

1. `raw_evidence_zone`
   - raw uploads
   - original source documents
   - ingestion checksums
2. `derived_artifact_zone`
   - page renders
   - OCR results
   - layout results
   - extraction outputs
   - prompt/response artifacts
3. `transactional_metadata_zone`
   - cases
   - documents
   - workflow states
   - validations
   - compliance results
   - review tasks
4. `audit_lineage_zone`
   - immutable audit events
   - lineage edges
   - version references
5. `curated_training_zone`
   - labeled datasets
   - annotation exports
   - training manifests
   - benchmark sets

## 1.2 Physical storage mapping

| Data zone | Primary store | Secondary / index |
|---|---|---|
| raw evidence | S3 / MinIO | PostgreSQL refs |
| derived artifacts | S3 / MinIO | PostgreSQL refs |
| transactional metadata | PostgreSQL | OpenSearch read model |
| audit lineage | PostgreSQL append-only + immutable store | OpenSearch |
| curated training | S3 / MinIO curated bucket + PostgreSQL dataset registry | OpenSearch optional |

## 1.3 Data design principles

1. No overwrite of raw evidence.
2. Derived artifacts are versioned, not replaced in place.
3. Every record references its upstream source through immutable IDs.
4. Every training dataset is reproducible from a manifest.
5. Search indexes are rebuildable from source systems.

## 2. Storage Layer Design

## 2.1 S3 / MinIO bucket layout

```text
s3://ops-agent/
  raw/
    yyyy/mm/dd/{case_id}/{document_id}/original.ext
  derived/
    yyyy/mm/dd/{case_id}/{document_id}/pages/page_001.png
    yyyy/mm/dd/{case_id}/{document_id}/ocr/ocr_vietocr-bank-v3.json
    yyyy/mm/dd/{case_id}/{document_id}/layout/layout_v1.json
    yyyy/mm/dd/{case_id}/{document_id}/extraction/schema_v2.json
    yyyy/mm/dd/{case_id}/{document_id}/llm/prompt_v1_response.json
  review/
    yyyy/mm/dd/{case_id}/review_bundle_v1.json
  datasets/
    versioned/{dataset_id}/manifest.json
    versioned/{dataset_id}/records/*.jsonl
    versioned/{dataset_id}/splits/train.jsonl
    versioned/{dataset_id}/splits/val.jsonl
    versioned/{dataset_id}/splits/test.jsonl
  benchmarks/
    golden/{benchmark_id}/...
  exports/
    qa_sampling/
    audit_exports/
```

## 2.2 PostgreSQL schema domains

Use separate logical schemas:

1. `ops_core`
2. `ops_ai`
3. `ops_review`
4. `ops_audit`
5. `ops_ml`

This keeps operational, lineage, and ML metadata separable without introducing multiple databases in MVP.

## 2.3 OpenSearch indexes

| Index | Purpose |
|---|---|
| `cases_v1` | case search and queue views |
| `documents_v1` | document metadata lookup |
| `audit_events_v1` | fast audit retrieval |
| `review_tasks_v1` | reviewer queue search |
| `dataset_records_v1` | optional dataset/debug lookup |

## 3. Data Schemas

## 3.1 Core entities

### `ops_core.cases`

| Column | Type | Notes |
|---|---|---|
| `case_id` | text PK | immutable case identifier |
| `workflow_type` | text | `kyc_onboarding`, `income_verification`, etc. |
| `priority` | text | low / normal / high / critical |
| `customer_reference` | text nullable | upstream business reference |
| `status` | text | operational workflow status |
| `compliance_status` | text | pending / completed_pass / review_required / etc. |
| `assigned_queue` | text | active queue |
| `final_outcome` | text nullable | approved / rejected / closed_without_decision |
| `created_at_utc` | timestamptz | |
| `updated_at_utc` | timestamptz | |

### `ops_core.documents`

| Column | Type | Notes |
|---|---|---|
| `document_id` | text PK | immutable document identifier |
| `case_id` | text FK | parent case |
| `filename` | text | original filename |
| `mime_type` | text | source mime |
| `source_channel` | text | upload channel |
| `retention_class` | text | records policy class |
| `sha256` | text | content hash |
| `raw_object_key` | text | S3 object key |
| `status` | text | processing state |
| `created_at_utc` | timestamptz | |

### `ops_core.document_versions`

Use when replacement or re-submission occurs instead of overwriting `documents`.

| Column | Type | Notes |
|---|---|---|
| `document_version_id` | text PK | immutable |
| `document_id` | text FK | logical document |
| `version_no` | int | monotonic |
| `raw_object_key` | text | artifact location |
| `sha256` | text | checksum |
| `supersedes_version_id` | text nullable | lineage |
| `created_at_utc` | timestamptz | |

## 3.2 AI artifact schemas

### `ops_ai.artifacts`

Generic artifact registry table.

| Column | Type | Notes |
|---|---|---|
| `artifact_id` | text PK | immutable artifact identifier |
| `case_id` | text | |
| `document_id` | text nullable | |
| `artifact_type` | text | page_render / ocr / layout / extraction / prompt_response / review_bundle |
| `artifact_version` | text | model / schema / prompt version |
| `object_key` | text | S3 location |
| `content_hash` | text | artifact hash |
| `producer_service` | text | owning service |
| `created_at_utc` | timestamptz | |

### `ops_ai.ocr_results`

| Column | Type | Notes |
|---|---|---|
| `ocr_result_id` | text PK | |
| `artifact_id` | text FK | points to OCR artifact |
| `document_id` | text | |
| `ocr_model_version` | text | VietOCR version |
| `preprocess_profile_version` | text | OpenCV profile |
| `ocr_confidence` | numeric | aggregated document OCR confidence |
| `page_count` | int | |
| `status` | text | completed / needs_review / error |
| `created_at_utc` | timestamptz | |

OCR block detail should live in JSON artifact files to avoid over-normalizing page text into relational tables too early.

### `ops_ai.classification_results`

| Column | Type | Notes |
|---|---|---|
| `classification_result_id` | text PK | |
| `document_id` | text | |
| `model_version` | text | classifier version |
| `document_type` | text | predicted class |
| `classification_confidence` | numeric | calibrated probability |
| `candidate_types_json` | jsonb | top-k candidates |
| `status` | text | |
| `created_at_utc` | timestamptz | |

### `ops_ai.extracted_fields`

One row per extracted field version.

| Column | Type | Notes |
|---|---|---|
| `field_result_id` | text PK | |
| `case_id` | text | |
| `document_id` | text | |
| `field_name` | text | |
| `field_value` | text nullable | raw extracted value |
| `normalized_value` | text nullable | canonical value |
| `confidence_score` | numeric | |
| `confidence_label` | text | high / medium / low / not_confident |
| `method` | text | rule_anchor / retrieval / llm_reconcile / reviewer_override |
| `artifact_id` | text FK | extraction artifact |
| `active_flag` | boolean | current effective field version |
| `created_at_utc` | timestamptz | |

### `ops_ai.field_evidence_refs`

| Column | Type | Notes |
|---|---|---|
| `evidence_ref_id` | text PK | |
| `field_result_id` | text FK | extracted field row |
| `document_id` | text | |
| `page_number` | int nullable | |
| `bbox_json` | jsonb nullable | |
| `text_span` | text nullable | |
| `artifact_ref` | text nullable | points into OCR/layout artifact |

## 3.3 Validation and decision schemas

### `ops_core.validation_results`

| Column | Type | Notes |
|---|---|---|
| `validation_result_id` | text PK | |
| `case_id` | text | |
| `rule_id` | text | |
| `rule_pack_version` | text | |
| `severity` | text | low / medium / high / critical |
| `result` | text | pass / fail / warning / review_required |
| `reason_code` | text | normalized reason code |
| `details_json` | jsonb | rule context |
| `created_at_utc` | timestamptz | |

### `ops_core.compliance_control_results`

| Column | Type | Notes |
|---|---|---|
| `control_result_id` | text PK | |
| `case_id` | text | |
| `control_id` | text | CCM-xx |
| `status` | text | pending / completed_pass / completed_fail / review_required |
| `reason_code` | text | |
| `evidence_json` | jsonb | references or summarized evidence |
| `created_at_utc` | timestamptz | |

### `ops_core.decision_results`

| Column | Type | Notes |
|---|---|---|
| `decision_result_id` | text PK | |
| `case_id` | text | |
| `route` | text | auto_process / cross_check / human_review / specialist_escalation |
| `decision_type` | text | recommendation / final_closure / review_required |
| `decision_confidence` | numeric | |
| `rationale_json` | jsonb | evidence-backed rationale |
| `policy_version` | text | routing policy version |
| `created_at_utc` | timestamptz | |

## 3.4 Review and audit schemas

### `ops_review.review_tasks`

| Column | Type | Notes |
|---|---|---|
| `review_task_id` | text PK | |
| `case_id` | text | |
| `assigned_queue` | text | |
| `assigned_to` | text nullable | |
| `status` | text | open / claimed / completed |
| `reason_codes_json` | jsonb | |
| `created_at_utc` | timestamptz | |
| `updated_at_utc` | timestamptz | |

### `ops_review.reviewer_actions`

| Column | Type | Notes |
|---|---|---|
| `review_action_id` | text PK | |
| `case_id` | text | |
| `review_task_id` | text nullable | |
| `reviewer_id` | text | |
| `action_type` | text | claim / correct_field / escalate / revalidate / close |
| `reason_code` | text | |
| `payload_json` | jsonb | |
| `created_at_utc` | timestamptz | |

### `ops_audit.audit_events`

| Column | Type | Notes |
|---|---|---|
| `audit_event_id` | text PK | immutable |
| `trace_id` | text | request / workflow trace |
| `case_id` | text | |
| `resource_type` | text | case / document / field / review_task / model_change |
| `resource_id` | text | |
| `action` | text | |
| `actor_type` | text | user / system |
| `actor_id` | text | |
| `prior_state_json` | jsonb nullable | |
| `new_state_json` | jsonb nullable | |
| `payload_json` | jsonb | |
| `created_at_utc` | timestamptz | |

## 3.5 ML dataset schemas

### `ops_ml.datasets`

| Column | Type | Notes |
|---|---|---|
| `dataset_id` | text PK | |
| `dataset_type` | text | ocr_benchmark / classification / extraction / anomaly |
| `dataset_version` | text | semantic or date version |
| `manifest_object_key` | text | S3 manifest |
| `source_query_hash` | text | reproducibility |
| `label_policy_version` | text | |
| `created_by` | text | |
| `created_at_utc` | timestamptz | |

### `ops_ml.annotations`

| Column | Type | Notes |
|---|---|---|
| `annotation_id` | text PK | |
| `dataset_id` | text | |
| `case_id` | text nullable | source case if from production |
| `document_id` | text | |
| `annotation_type` | text | document_type / field / quality / anomaly |
| `annotation_payload_json` | jsonb | |
| `annotator_id` | text | |
| `qa_status` | text | pending / approved / rejected |
| `created_at_utc` | timestamptz | |

## 4. ETL / ELT Workflow

## 4.1 Operational ETL

### Ingestion to operations

1. receive document bundle
2. validate metadata and file integrity
3. write raw files to S3 / MinIO
4. write document and case rows to PostgreSQL
5. emit `document.received`
6. materialize read models into OpenSearch asynchronously

### AI artifact ELT

1. OCR/layout/classification/extraction services write artifacts to S3 first
2. services write artifact metadata and summary fields to PostgreSQL
3. read-model pipelines index summary documents into OpenSearch

This is ELT-like because artifact truth stays in storage and metadata is normalized for serving and querying.

## 4.2 Dataset generation ETL

1. select source cases by governed query
2. freeze source manifest with:
   - case IDs
   - document IDs
   - source artifact hashes
   - rule/model versions
3. export normalized JSONL dataset records into curated S3 dataset path
4. register dataset version in `ops_ml.datasets`
5. create train/val/test splits by manifest, not ad hoc sampling

## 4.3 OpenSearch indexing pipeline

Indexing should be asynchronous and replayable:

1. consume PostgreSQL outbox or Kafka domain events
2. transform to search documents
3. upsert into index
4. maintain index version aliases for reindexing

## 5. Annotation Workflow

## 5.1 Human annotation flow

1. dataset builder selects governed source records
2. annotation package is generated from raw docs and artifacts
3. annotator labels:
   - document type
   - OCR text corrections where needed
   - field values
   - evidence bounding boxes
   - quality labels
4. second-pass QA reviews high-risk labels
5. approved annotations are frozen into dataset version

## 5.2 Reviewer-to-annotation conversion

Operational reviewer corrections are not immediately training labels. They must pass through normalization:

1. collect reviewer correction event
2. join to source evidence artifacts
3. transform into annotation candidate
4. send to QA or trusted-label workflow
5. include only approved corrections in training datasets

This prevents noisy operational edits from polluting model training.

## 5.3 Annotation payload guidance

Each field annotation must include:

1. `field_name`
2. `canonical_value`
3. `source_text`
4. `document_id`
5. `page_number`
6. `bbox`
7. `annotation_confidence`
8. `annotation_source`:
   - manual_label
   - reviewer_confirmed
   - qa_confirmed

## 6. Data Lineage Plan

## 6.1 Lineage requirements

Every derived output must be traceable to:

1. source document version
2. upstream artifact(s)
3. producing service
4. producing model/rule/prompt version
5. producing workflow run

## 6.2 Lineage model

Represent lineage as edges between entities:

```text
raw_document
  -> page_render
  -> ocr_artifact
  -> layout_artifact
  -> classification_result
  -> extracted_field
  -> validation_result
  -> compliance_control_result
  -> decision_result
  -> review_action
  -> training_dataset_record
```

## 6.3 Suggested lineage table

### `ops_audit.lineage_edges`

| Column | Type | Notes |
|---|---|---|
| `lineage_edge_id` | text PK | |
| `upstream_entity_type` | text | |
| `upstream_entity_id` | text | |
| `downstream_entity_type` | text | |
| `downstream_entity_id` | text | |
| `edge_type` | text | produced_from / corrected_from / included_in_dataset |
| `created_at_utc` | timestamptz | |

## 6.4 Reproducibility rule

Any decision, benchmark, or model run must be reproducible from:

1. manifest,
2. source artifact hashes,
3. version registry references,
4. lineage edges.

## 7. Feedback Loop Design

## 7.1 Correction-to-retraining loop

1. reviewer corrects field or class
2. reviewer action is stored in `ops_review.reviewer_actions`
3. feedback pipeline joins:
   - correction
   - original extraction
   - OCR artifact
   - source document
4. create normalized feedback candidate in `ops_ml.annotations`
5. QA validates candidate
6. approved labels flow into next dataset build
7. retraining pipeline consumes dataset manifest

## 7.2 Escalation feedback loop

1. compliance or fraud escalations are resolved by specialists
2. final specialist disposition is stored
3. anomaly-support label generator produces:
   - true positive
   - false positive
   - missed signal candidate
4. anomaly model training set is updated on a governed cadence

## 7.3 Prompt and LLM feedback loop

1. low-confidence or overruled prompt outputs are logged
2. prompt artifact refs are attached to reviewer outcomes
3. prompt QA analysis classifies failure cause
4. only prompt-approved regression cases enter prompt benchmark sets

## 8. Data Quality Monitoring Plan

## 8.1 Quality dimensions

Track:

1. completeness
2. consistency
3. timeliness
4. uniqueness
5. referential integrity
6. lineage coverage

## 8.2 Core data quality checks

| Check | Rule |
|---|---|
| checksum presence | every document must have sha256 |
| raw object availability | every document row must resolve to a raw object key |
| artifact lineage coverage | every AI artifact must link back to source document |
| evidence linkage | every critical extracted field must have at least one evidence ref |
| active field uniqueness | one active extracted field row per case/document/field_name |
| compliance visibility | every active case must have explicit compliance control rows for required controls |
| audit event coverage | every material workflow step must emit an audit event |
| dataset manifest integrity | every dataset record must reference source hashes and object keys |

## 8.3 Monitoring outputs

Publish metrics for:

1. missing object refs
2. orphan artifacts
3. extracted fields without evidence
4. audit gaps by workflow step
5. annotation QA rejection rate
6. dataset build failures
7. training dataset staleness

## 8.4 Alerting thresholds

Alert when:

1. any raw-document write succeeds but metadata row is missing
2. any decision result lacks upstream compliance result
3. any critical field has no evidence ref
4. lineage edge coverage drops below expected threshold
5. dataset builds include unknown schema version

## 9. Recommended Implementation Sequence

1. define PostgreSQL schema domains and IDs
2. define S3 bucket layout and artifact naming standard
3. implement artifact registry and lineage edges
4. implement outbox-driven OpenSearch indexing
5. implement dataset registry and manifest builder
6. implement annotation import / QA pipeline
7. implement correction feedback normalizer
8. implement data quality dashboards and alerts

## 10. Recommended Data Stance

The data platform for Ops Agent should be treated as an evidence system first, an analytics system second, and a training-data source third.

That ordering matters because:

1. operations need source truth,
2. compliance needs replayable lineage,
3. ML needs curated reproducible datasets,
4. all three depend on preserving raw evidence and derived linkage without loss.

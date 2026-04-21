# Multi-Agent Workflow Specification for Ops Agent

## Current Architecture Override: LLM Extraction Baseline

The Documents module now follows the production LLM extraction design in [production-llm-document-extraction-backend-spec.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\production-llm-document-extraction-backend-spec.md).

For identity-card document extraction, the active architecture is not a model-training pipeline and not a traditional OCR pipeline. It is an inference-only GPT-4o Vision structured extraction workflow:

1. Input documents are images or PDFs.
2. Python and Pillow validate, resize, normalize, and encode images as base64 data URLs.
3. LangGraph orchestrates preprocessing, extraction, validation, retry, normalization, and output finalization.
4. OpenAI GPT-4o or GPT-4o-mini performs OCR-like visual reading and semantic field extraction.
5. Structured output is enforced with strict Pydantic or JSON Schema rules.
6. Unknown or uncertain values are `null`.
7. Extra fields are rejected.
8. The pipeline retries once when schema validation fails.
9. Normalized output is displayed as an editable table for manual review.
10. Only approved reviewed data is persisted to production PostgreSQL tables.
11. Every document and extraction run is searchable by UUID and fully audit-linked.

Any older references in this document to VietOCR as the primary OCR path, classical ML classification, local LLM fallback, confidence benchmarking, or model-training workflows are legacy architecture notes and are superseded for the Documents extraction module by the baseline above.

## 1. Workflow Goals

1. Define a conservative multi-agent workflow that supports banking document intake, extraction, validation, compliance gating, decision support, and human review.
2. Keep agent boundaries explicit so no agent silently expands into another role.
3. Make every material output structured, evidence-backed, and auditable.
4. Route uncertain, conflicting, incomplete, or high-risk cases to human review rather than unsafe automation.
5. Give backend and prompt engineers stable contracts for orchestration, retries, logging, and escalation behavior.

## 2. Workflow Architecture Diagram

```text
                                      +------------------------+
                                      |  React / Next.js UI    |
                                      |  - review workstation  |
                                      |  - document viewer     |
                                      |  - audit trace viewer  |
                                      +-----------+------------+
                                                  |
                                                  v
 +---------------------+                 +--------+--------+                 +----------------------+
 | External Channels   |   HTTPS/TLS     | Kong / Nginx    |                 | Keycloak (OAuth2)    |
 | - branch upload     +---------------->+ API Gateway     +<--------------->+ RBAC / tokens        |
 | - ops portal        |                 | authn/authz     |                 +----------------------+
 | - email adapter     |                 +--------+--------+
 | - upstream APIs     |                          |
 +---------------------+                          v
                                        +---------+----------+
                                        | FastAPI services   |
                                        | - ingestion svc    |
                                        | - case svc         |
                                        | - review svc       |
                                        | - audit svc        |
                                        +---------+----------+
                                                  |
                                                  v
                                       +----------+-----------+
                                       | Temporal workflows   |
                                       | durable orchestration|
                                       +----------+-----------+
                                                  |
                           +----------------------+----------------------+
                           |                                             |
                           v                                             v
                 +---------+----------+                       +----------+----------+
                 | Kafka event bus    |                       | Celery worker pool  |
                 | domain events      |                       | CPU/GPU async tasks  |
                 +---------+----------+                       +----------+----------+
                           |                                             |
      +--------------------+--------------------+------------------------+---------------------+
      |                    |                    |                        |                     |
      v                    v                    v                        v                     v
 +----+-----+       +------+-------+     +------+--------+       +-------+-------+      +------+--------+
 | Ingestion|       | OCR service  |     | Layout svc    |       | ML / LLM svc  |      | Rule engine   |
 | agent    |       | VietOCR      |     | OpenCV + CV   |       | XGBoost/LGBM  |      | schemas, KYC  |
 | checksum |       | PyTorch GPU  |     | segmentation  |       | local LLM     |      | AML rules     |
 +----+-----+       +------+-------+     +------+--------+       +-------+-------+      +------+--------+
      |                    |                    |                        |                     |
      +--------------------+--------------------+------------------------+---------------------+
                                                  |
                                                  v
                                    +-------------+--------------+
                                    | Decision / compliance svc  |
                                    | - confidence aggregation   |
                                    | - automation boundaries    |
                                    | - escalation policy        |
                                    +-------------+--------------+
                                                  |
                          +-----------------------+------------------------+
                          |                                                |
                          v                                                v
                +---------+----------+                           +---------+----------+
                | PostgreSQL         |                           | S3 / MinIO         |
                | metadata, cases,   |                           | raw docs, artifacts |
                | rules, versions    |                           | prompts, evidence   |
                +---------+----------+                           +---------+----------+
                          |                                                |
                          v                                                v
                +---------+----------+                           +---------+----------+
                | OpenSearch         |                           | Weaviate           |
                | search, audit idx  |                           | semantic retrieval |
                +---------+----------+                           +---------+----------+
                          |                                                |
                          +-----------------------+------------------------+
                                                  |
                                                  v
                                    +-------------+--------------+
                                    | Observability stack        |
                                    | ELK + Prometheus/Grafana   |
                                    | OpenTelemetry traces       |
                                    +----------------------------+
```

## 3. Agent Workflow Overview

### 3.1 Design decisions

1. Use FastAPI microservices for clean domain separation: intake, workflow, AI processing, compliance, decisioning, audit, and review.
2. Use Temporal as the durable workflow engine because banking workflows require retries, signals, timers, human-in-the-loop pauses, and exact replay of execution state.
3. Use Kafka for event distribution and audit-friendly event streams; use Celery workers for heavy OCR / image / ML execution with GPU/CPU queues.
4. Use VietOCR as the OCR system of record for text extraction. No alternate OCR engine is treated as primary.
5. Use OpenCV before VietOCR for deskew, denoise, crop normalization, and binarization.
6. Use deterministic rules first, classical ML second, LLM last.
7. Use LLMs only for bounded ambiguity resolution, not for final compliance or risk decisions.
8. Use S3-compatible object storage for original documents and derived artifacts; never overwrite originals.
9. Store every agent result as immutable versioned evidence with trace IDs and model/rule versions.

### 3.2 Service decomposition

| Service | Responsibility | Stack |
|---|---|---|
| `api-gateway` | authn, authz, rate limits, routing | Kong or Nginx |
| `case-service` | case lifecycle, metadata APIs | FastAPI + PostgreSQL |
| `ingestion-service` | upload, checksum, document registration, S3 write | FastAPI |
| `workflow-service` | Temporal workflow launch, state transitions | FastAPI + Temporal |
| `ocr-service` | preprocessing + VietOCR inference | FastAPI worker + Celery + PyTorch |
| `layout-service` | page segmentation, block detection, table/kv regions | OpenCV + Python CV service |
| `classification-service` | document-type inference | XGBoost/LightGBM + rules |
| `extraction-service` | field extraction, field-level evidence, LLM fallback | rules + ML + local LLM |
| `validation-service` | schema validation, cross-document matching, confidence calibration | FastAPI + rules + ML |
| `compliance-service` | KYC/AML control status, escalations, human-review gates | FastAPI + rules |
| `decision-service` | confidence aggregation, routing, disposition recommendation | FastAPI |
| `audit-service` | immutable event logging and evidence indexing | FastAPI + PostgreSQL + OpenSearch |
| `review-service` | reviewer tasks, assignments, corrections, approvals | FastAPI |
| `search-service` | lexical and semantic retrieval | OpenSearch + Weaviate |
| `frontend` | human review workstation | Next.js / React |

## 4. Full List of Agents and Boundaries

### 4.1 Boundary rules for all agents

1. Each agent owns exactly one decision domain and must not silently perform another agent's job.
2. Agents may enrich upstream outputs, but may not overwrite source evidence or prior audit history.
3. Any agent producing a critical field, exception, escalation recommendation, or confidence-driven route must include evidence references.
4. No agent other than the Human Review Agent may finalize regulated approvals, rejections, overrides, or escalated-case dispositions.
5. Compliance Agent and Decision Agent may block automation, but must not silently clear high-risk compliance states without explicit completed checks.
6. Prompt-driven behavior is allowed only in bounded substeps and must still emit the same strict output schema.

### 4.2 Agent specifications table

| Agent | Role | Input schema | Output schema | Tools / models | Confidence calculation | Failure modes |
|---|---|---|---|---|---|---|
| Ingestion Agent | Register case, validate payload, store raw file, emit workflow event | `IngestionInput` | `IngestionOutput` | FastAPI, PostgreSQL, S3, AV scanner, checksum | deterministic `1.0` if checks pass, else `0.0` | unsupported mime, checksum mismatch, upload timeout, storage failure |
| OCR Agent | Preprocess image and run VietOCR | `OCRInput` | `OCROutput` | OpenCV, VietOCR, PyTorch GPU, Celery | weighted OCR score from char conf, line conf, coverage, image quality | unreadable page, GPU OOM, timeout, low coverage |
| Layout Parsing Agent | Detect regions, pages, tables, key-value blocks, signatures | `LayoutInput` | `LayoutOutput` | OpenCV, contour analysis, classical CV models | geometric consistency + block detection certainty | page segmentation failure, rotated pages, merged blocks |
| Classification Agent | Determine document type and subtype | `ClassificationInput` | `ClassificationOutput` | LightGBM/XGBoost, rules, embeddings retrieval | calibrated class probability adjusted by OCR/layout quality | ambiguous class, unseen template, low OCR quality |
| Extraction Agent | Extract field values with evidence refs | `ExtractionInput` | `ExtractionOutput` | regex, schema rules, layout anchors, local LLM fallback, Weaviate retrieval | field-level confidence aggregated to extraction score | missing anchors, conflicting values, hallucination risk in LLM fallback |
| Validation Agent | Validate fields, freshness, schema, and cross-document consistency | `ValidationInput` | `ValidationOutput` | deterministic rules, OpenSearch lookup, ML anomaly scorers | rule pass ratio weighted by criticality + confidence penalty | rule conflicts, missing dependencies, low trust on critical field |
| Compliance Agent | Evaluate KYC/AML/compliance statuses and escalation gates | `ComplianceInput` | `ComplianceOutput` | compliance rules, sanctions adapter, case policy store | deterministic severity-based status, no opaque score-only approval | pending sanctions check, critical alert, policy version missing |
| Decision Agent | Choose auto-process, cross-check, review, or escalate | `DecisionInput` | `DecisionOutput` | decision rules, confidence aggregator, policy thresholds | hierarchical score using OCR/classification/extraction/validation/compliance | unresolved critical checks, inconsistent upstream outputs |
| Audit Agent | Persist immutable trace and evidence index | `AuditInput` | `AuditOutput` | PostgreSQL append-only tables, S3 artifact store, OpenSearch | not decisioning; event write success boolean | storage failure, event ordering issue |
| Human Review Agent | Present tasks, accept corrections/approvals, close loop | `HumanReviewInput` | `HumanReviewOutput` | Next.js UI, review APIs, annotation viewer | human_decision_confidence fixed to `1.0` with reviewer attestation, not model confidence | reviewer timeout, missing evidence, unauthorized action |

### 4.3 Agent responsibility clarifications

#### Ingestion Agent

1. Accepts case metadata and file registrations only.
2. Does not classify content or make business decisions.
3. May reject uploads only for technical or policy-gate reasons known at intake.

#### OCR Agent

1. Converts document images into machine-readable text and positional evidence using VietOCR.
2. Does not infer document type or business meaning.

#### Layout Parsing Agent

1. Identifies structural regions such as header, table, key-value zones, signatures, and page boundaries.
2. Does not decide field semantics beyond structural grouping.

#### Classification Agent

1. Determines document type and subtype.
2. Does not extract business fields beyond classification metadata.

#### Extraction Agent

1. Produces field values, normalized values, field-level confidence, and evidence references.
2. May use rules, anchors, and bounded LLM fallback.
3. Does not decide whether extracted values are acceptable for workflow completion.

#### Validation Agent

1. Applies deterministic schema, completeness, freshness, and cross-document consistency rules.
2. Produces explicit pass, fail, warn, and review-needed signals.
3. Does not approve cases.

#### Compliance Agent

1. Tracks compliance-critical check status and escalation gates.
2. May block progression or require specialist review.
3. Does not auto-resolve sanctions, PEP, AML, or suspicious-activity outcomes.

#### Decision Agent

1. Aggregates upstream outputs and selects the next route:
   auto-process candidate, cross-check, human review, or specialist escalation.
2. Applies policy boundaries and confidence thresholds.
3. Does not substitute for human approval where policy requires it.

#### Audit Agent

1. Records immutable workflow and evidence events.
2. Does not participate in routing or business decisions.

#### Human Review Agent

1. Represents reviewer interaction with the case through UI and APIs.
2. Can correct, attest, escalate, approve, reject, or close only within role permissions.
3. Is the only agent allowed to finalize decisions that policy marks as human-owned.

## 5. Input / Output Contracts

### 5.1 Common envelope

```json
{
  "trace_id": "uuid",
  "case_id": "case_123",
  "document_id": "doc_123",
  "workflow_type": "kyc_onboarding",
  "agent_version": "string",
  "timestamp_utc": "2026-04-14T11:00:00Z"
}
```

### 5.2 Ingestion Agent

`IngestionInput`

```json
{
  "trace_id": "uuid",
  "case_id": null,
  "workflow_type": "kyc_onboarding",
  "priority": "normal",
  "source_channel": "ops_upload",
  "customer_reference": "cust_001",
  "documents": [
    {
      "filename": "passport.pdf",
      "mime_type": "application/pdf",
      "byte_size": 183002,
      "sha256": "hex",
      "s3_object_key": "raw/2026/04/14/passport.pdf"
    }
  ]
}
```

`IngestionOutput`

```json
{
  "trace_id": "uuid",
  "case_id": "case_123",
  "status": "accepted",
  "document_records": [
    {
      "document_id": "doc_123",
      "mime_type": "application/pdf",
      "storage_status": "stored",
      "checksum_verified": true,
      "quarantine": false
    }
  ],
  "errors": []
}
```

### 5.3 OCR Agent

`OCRInput`

```json
{
  "trace_id": "uuid",
  "case_id": "case_123",
  "document_id": "doc_123",
  "pages": [
    {
      "page_number": 1,
      "image_uri": "s3://bucket/derived/doc_123/page_1.png",
      "preprocess_profile": "deskew_denoise_v1"
    }
  ]
}
```

`OCROutput`

```json
{
  "trace_id": "uuid",
  "document_id": "doc_123",
  "ocr_model": {
    "engine": "vietocr",
    "model_version": "vietocr-bank-v3"
  },
  "pages": [
    {
      "page_number": 1,
      "text_blocks": [
        {
          "block_id": "blk_1",
          "text": "PASSPORT",
          "bbox": [0.12, 0.08, 0.48, 0.14],
          "line_confidence": 0.992
        }
      ],
      "coverage_ratio": 0.96,
      "image_quality_score": 0.91,
      "page_confidence": 0.947
    }
  ],
  "ocr_confidence": 0.947,
  "status": "completed"
}
```

### 5.4 Layout Parsing Agent

`LayoutInput`

```json
{
  "trace_id": "uuid",
  "document_id": "doc_123",
  "pages": [
    {
      "page_number": 1,
      "image_uri": "s3://bucket/derived/doc_123/page_1.png",
      "ocr_blocks_ref": "s3://bucket/artifacts/doc_123/ocr.json"
    }
  ]
}
```

`LayoutOutput`

```json
{
  "trace_id": "uuid",
  "document_id": "doc_123",
  "pages": [
    {
      "page_number": 1,
      "regions": [
        {
          "region_id": "reg_identity_header",
          "region_type": "key_value_zone",
          "bbox": [0.05, 0.05, 0.95, 0.35],
          "confidence": 0.93
        }
      ],
      "signature_regions": [],
      "table_regions": []
    }
  ],
  "layout_confidence": 0.93,
  "status": "completed"
}
```

### 5.5 Classification Agent

`ClassificationInput`

```json
{
  "trace_id": "uuid",
  "document_id": "doc_123",
  "ocr_confidence": 0.947,
  "layout_confidence": 0.93,
  "features": {
    "token_hashes": ["passport", "issuing", "nationality"],
    "page_count": 1,
    "has_mrz": true
  }
}
```

`ClassificationOutput`

```json
{
  "trace_id": "uuid",
  "document_id": "doc_123",
  "document_type": "passport",
  "document_subtype": "individual_identity",
  "candidate_types": [
    {
      "label": "passport",
      "probability": 0.984
    },
    {
      "label": "national_id",
      "probability": 0.011
    }
  ],
  "classification_confidence": 0.962,
  "status": "completed"
}
```

### 5.6 Extraction Agent

`ExtractionInput`

```json
{
  "trace_id": "uuid",
  "case_id": "case_123",
  "document_id": "doc_123",
  "document_type": "passport",
  "ocr_artifact_ref": "s3://bucket/artifacts/doc_123/ocr.json",
  "layout_artifact_ref": "s3://bucket/artifacts/doc_123/layout.json",
  "schema_version": "passport_fields_v2",
  "llm_fallback_allowed": true
}
```

`ExtractionOutput`

```json
{
  "trace_id": "uuid",
  "document_id": "doc_123",
  "fields": [
    {
      "field_name": "full_name",
      "value": "NGUYEN VAN A",
      "normalized_value": "NGUYEN VAN A",
      "method": "rule_anchor",
      "confidence": 0.985,
      "evidence_refs": [
        {
          "page_number": 1,
          "bbox": [0.20, 0.32, 0.82, 0.39],
          "text_span": "NGUYEN VAN A"
        }
      ]
    }
  ],
  "missing_fields": [],
  "conflicts": [],
  "extraction_confidence": 0.968,
  "status": "completed"
}
```

### 5.7 Validation Agent

`ValidationInput`

```json
{
  "trace_id": "uuid",
  "case_id": "case_123",
  "document_bundle": [
    {
      "document_id": "doc_123",
      "document_type": "passport",
      "extraction_ref": "s3://bucket/artifacts/doc_123/extraction.json"
    }
  ],
  "policy_version": "bank_policy_2026_04"
}
```

`ValidationOutput`

```json
{
  "trace_id": "uuid",
  "case_id": "case_123",
  "rule_results": [
    {
      "rule_id": "passport.expiry.valid",
      "severity": "critical",
      "result": "pass",
      "reason_code": "document_not_expired",
      "evidence_refs": [
        {
          "document_id": "doc_123",
          "field_name": "expiry_date"
        }
      ]
    }
  ],
  "validation_confidence": 0.979,
  "overall_status": "completed_pass"
}
```

### 5.8 Compliance Agent

`ComplianceInput`

```json
{
  "trace_id": "uuid",
  "case_id": "case_123",
  "workflow_type": "kyc_onboarding",
  "validation_ref": "s3://bucket/cases/case_123/validation.json",
  "screening_signals": {
    "sanctions_status": "pending",
    "pep_status": "not_started",
    "fraud_alerts": []
  }
}
```

`ComplianceOutput`

```json
{
  "trace_id": "uuid",
  "case_id": "case_123",
  "control_results": [
    {
      "control_id": "CCM-01",
      "status": "completed_pass",
      "reason_code": "required_identity_fields_present"
    },
    {
      "control_id": "CCM-04",
      "status": "pending",
      "reason_code": "sanctions_check_in_progress"
    }
  ],
  "compliance_status": "partial_compliance",
  "requires_human_review": true,
  "status": "completed"
}
```

### 5.9 Decision Agent

`DecisionInput`

```json
{
  "trace_id": "uuid",
  "case_id": "case_123",
  "ocr_confidence": 0.947,
  "classification_confidence": 0.962,
  "extraction_confidence": 0.968,
  "validation_confidence": 0.979,
  "compliance_status": "partial_compliance",
  "critical_failures": [],
  "pending_critical_checks": ["CCM-04"]
}
```

`DecisionOutput`

```json
{
  "trace_id": "uuid",
  "case_id": "case_123",
  "route": "human_review",
  "decision_type": "review_required",
  "decision_confidence": 0.0,
  "rationale": [
    "pending_critical_check:CCM-04",
    "human_review_required_for_kyc_release"
  ],
  "next_action": "create_review_task",
  "status": "completed"
}
```

### 5.10 Audit Agent

`AuditInput`

```json
{
  "trace_id": "uuid",
  "case_id": "case_123",
  "event_type": "decision_recorded",
  "actor_type": "system",
  "actor_id": "decision_service",
  "payload_ref": "s3://bucket/cases/case_123/decision.json"
}
```

`AuditOutput`

```json
{
  "trace_id": "uuid",
  "event_id": "audit_123",
  "write_status": "persisted",
  "immutable_hash": "hex"
}
```

### 5.11 Human Review Agent

`HumanReviewInput`

```json
{
  "trace_id": "uuid",
  "case_id": "case_123",
  "review_task_id": "task_123",
  "assigned_to": "reviewer_007",
  "case_bundle_ref": "s3://bucket/cases/case_123/review_bundle.json"
}
```

`HumanReviewOutput`

```json
{
  "trace_id": "uuid",
  "case_id": "case_123",
  "review_task_id": "task_123",
  "action": "correct_and_revalidate",
  "reviewer_id": "reviewer_007",
  "corrections": [
    {
      "field_name": "full_name",
      "new_value": "NGUYEN VAN AN",
      "reason_code": "reviewer_confirmed_typo",
      "evidence_refs": [
        {
          "document_id": "doc_123",
          "page_number": 1
        }
      ]
    }
  ],
  "comment": "OCR dropped trailing character",
  "status": "submitted"
}
```

## 6. Sequence Flow Between Agents

### 6.1 Workflow graph

1. `document.received`
2. Ingestion Agent registers case, validates payload, stores raw artifact, emits `document.stored`
3. Workflow engine fans out pages to OCR Agent
4. OCR Agent preprocesses page images and runs VietOCR
5. Layout Parsing Agent segments document into logical regions
6. Classification Agent assigns document type
7. Extraction Agent performs deterministic extraction
8. If extraction confidence is medium, run cross-check subgraph:
   - alternate preprocessing profile
   - re-run VietOCR on suspect regions
   - run schema-aware alternate extraction
   - optional bounded LLM reconciliation
9. Validation Agent runs field and cross-document rules
10. Compliance Agent evaluates KYC/AML/compliance control statuses
11. Decision Agent routes to:
   - straight-through operational completion,
   - cross-check subgraph,
   - human review,
   - specialist escalation
12. Audit Agent records every material step
13. Human Review Agent handles corrections, approvals, escalations, and revalidation
14. Workflow closes only after compliance and operational statuses satisfy policy

### 6.2 Kafka topics

1. `document.received`
2. `document.stored`
3. `ocr.completed`
4. `layout.completed`
5. `classification.completed`
6. `extraction.completed`
7. `validation.completed`
8. `compliance.completed`
9. `decision.completed`
10. `review.required`
11. `review.completed`
12. `audit.persisted`
13. `pipeline.failed`
14. `pipeline.dlq`

### 6.3 Temporal orchestration pattern

Use one Temporal workflow per case and one child workflow per document. Human review is modeled as a wait state using Temporal signals:

1. `submit_document`
2. `run_document_pipeline`
3. `aggregate_case_results`
4. `await_review_signal`
5. `revalidate_after_review`
6. `close_case`

## 7. Conditional Routing Logic

```python
def route_case(case_ctx):
    if case_ctx.ingestion_status != "accepted":
        return route("manual_intake_resolution", reason="intake_failed")

    if case_ctx.critical_processing_failure:
        return route("human_review", reason="critical_processing_failure")

    if any(doc.classification_confidence < 0.80 for doc in case_ctx.documents):
        return route("human_review", reason="low_classification_confidence")

    if any(doc.ocr_confidence < 0.80 for doc in case_ctx.documents):
        return route("cross_check", reason="low_ocr_confidence")

    if any(doc.extraction_confidence < 0.80 for doc in case_ctx.documents):
        return route("human_review", reason="low_extraction_confidence")

    if any(0.80 <= doc.extraction_confidence < 0.93 for doc in case_ctx.documents):
        return route("cross_check", reason="medium_extraction_confidence")

    if case_ctx.has_critical_validation_failures:
        return route("human_review", reason="critical_validation_failure")

    if case_ctx.compliance_status in {"pending", "partial_compliance", "review_required", "non_compliant"}:
        return route("human_review", reason=f"compliance_status:{case_ctx.compliance_status}")

    if case_ctx.has_sanctions_alert or case_ctx.has_fraud_alert or case_ctx.has_aml_alert:
        return route("specialist_escalation", reason="compliance_alert")

    overall_score = aggregate_confidence(case_ctx)

    if overall_score >= 0.95 and case_ctx.workflow_type in STP_ALLOWED_WORKFLOWS:
        return route("auto_process", reason="high_confidence_low_risk")

    if 0.85 <= overall_score < 0.95:
        return route("cross_check", reason="medium_overall_confidence")

    return route("human_review", reason="default_conservative_gate")


def cross_check(case_ctx):
    rerun_ocr_on_low_confidence_regions(case_ctx)
    rerun_schema_extraction(case_ctx)
    if ambiguous_fields_remain(case_ctx):
        run_bounded_llm_reconciliation(case_ctx)
    revalidate(case_ctx)
    return route_case(case_ctx)
```

## 8. Rules vs ML vs LLM Decision Framework

| Problem type | Primary method | Why | Do not use | Trade-offs |
|---|---|---|---|---|
| MIME checks, file validity, schema requirements, regex patterns, expiry dates | Deterministic rules | Fully auditable, low latency, no hallucination | LLM | Best for hard controls; brittle if templates vary |
| Document classification with many issuer templates | Classical ML + rules | Fast, calibratable, cheaper than LLM, easier to explain than free-form LLM | LLM as first pass | Needs labeled data and retraining |
| Signature presence, page quality, anomaly scores | Classical ML / CV | Numeric output, easier thresholding | LLM | Good for ranking; may miss context |
| Key-value extraction from known templates | Rules + layout anchors | Deterministic, cheapest, reproducible | LLM-only extraction | Requires per-template tuning |
| Ambiguous text resolution, fallback extraction on messy scans, reviewer summarization | LLM, bounded and evidence-constrained | Handles ambiguity and unstructured text better | Unbounded free-form decisioning | Higher latency/cost, hallucination risk, extra audit burden |
| Final compliance disposition | Human + rules | Regulatory defensibility | LLM or pure ML | Slowest but safest |

### 8.1 Explicit policy

1. Use rules whenever schema, pattern, or threshold logic is sufficient.
2. Use classical ML for probabilistic classification, quality scoring, and anomaly ranking.
3. Use LLM only after rules and ML leave unresolved ambiguity and only inside a bounded JSON contract.
4. Never let LLM output directly close or reject a regulated case.

## 9. Confidence-Based Fallback Logic

### 9.1 OCR confidence

For each page:

```text
ocr_page_confidence =
  0.45 * mean(line_confidence)
+ 0.20 * median(line_confidence)
+ 0.20 * coverage_ratio
+ 0.15 * image_quality_score
```

For the document:

```text
ocr_confidence = min(critical_page_confidence, weighted_mean(page_confidence))
```

Use `min` on critical pages because one failed ID page can invalidate the document.

### 9.2 Classification confidence

```text
classification_confidence =
  0.70 * calibrated_model_probability
+ 0.15 * template_similarity_score
+ 0.10 * ocr_confidence
+ 0.05 * layout_confidence
```

### 9.3 Extraction confidence

For each field:

```text
field_confidence =
  0.35 * source_text_confidence
+ 0.25 * anchor_match_score
+ 0.20 * pattern_validation_score
+ 0.10 * cross_field_consistency_score
+ 0.10 * method_reliability_score
```

Document extraction confidence:

```text
extraction_confidence =
  min(critical_field_confidence, weighted_mean(all_field_confidence))
```

### 9.4 Aggregate decision confidence

```text
overall_confidence =
  0.20 * ocr_confidence
+ 0.15 * classification_confidence
+ 0.30 * extraction_confidence
+ 0.20 * validation_confidence
+ 0.15 * compliance_readiness_score
```

Where:

1. `compliance_readiness_score = 1.0` only if all required controls are `completed_pass`.
2. `compliance_readiness_score = 0.0` if any critical control is pending, failed, or review-required.

This makes compliance status a gating factor, not a cosmetic score.

### 9.5 Thresholds

| Range / condition | Route |
|---|---|
| `overall_confidence >= 0.95` and all required compliance checks passed and STP allowed | Auto-process |
| `0.85 <= overall_confidence < 0.95` and no critical failures | Cross-check subgraph |
| `overall_confidence < 0.85` | Human review |
| Any critical validation fail, sanctions/AML/fraud alert, or pending critical compliance check | Human review or specialist escalation regardless of score |

### 9.6 Auto-approve / auto-reject interpretation

1. `Auto approve` means auto-process operationally eligible low-risk cases, not final approval of sanctions/AML/fraud-sensitive decisions.
2. `Auto reject` is restricted to technical document rejection or automated request-for-resubmission conditions:
   - unsupported file,
   - corrupted file,
   - password-protected unreadable file,
   - missing mandatory document package at submission gate.
3. Final adverse customer outcomes remain human-approved.

### 9.7 Fallback strategy

1. Re-run OpenCV preprocessing with alternate profiles on low OCR confidence pages.
2. Re-run VietOCR on cropped suspect regions instead of whole page first.
3. Use rule-based alternate extraction profile for the classified document template.
4. Use LLM reconciliation only on unresolved fields and only with OCR text + evidence refs.
5. Escalate to human if critical fields remain ambiguous.

## 10. Failure, Retry, and Safe Degradation Behavior

### 10.1 Failure scenarios

| Scenario | Detection | Recovery | Final safe mode |
|---|---|---|---|
| OCR failure | timeout, empty text, low coverage | retry on CPU/GPU queue, alternate preprocess profile | human review with original doc |
| Corrupted document | parser/open failure | quarantine and request resubmission | manual-only mode |
| Missing fields | extraction result missing mandatory fields | alternate extraction, LLM fallback on specific fields, request more docs | human review |
| Model disagreement | classifier/extractor disagree across passes | run cross-check subgraph, compare evidence | human review |
| Kafka unavailable | publish failures | local transactional outbox in PostgreSQL, replay when bus recovers | degraded synchronous processing |
| Temporal unavailable | workflow start/heartbeat failure | stop intake progression, persist pending jobs | manual queue hold |
| GPU outage | OCR service health failures | route OCR to CPU workers with reduced SLA | slower processing, no silent drop |
| LLM unavailable | timeout/5xx | skip LLM branch, stay rules+ML only | human review |
| OpenSearch/Weaviate outage | query failure | continue without retrieval-dependent enrichment | human review or rules-only mode |
| Compliance adapter pending | sanctions/AML service unavailable | mark critical check pending | block auto-process |

### 10.2 Retry strategy

1. Stateless idempotent tasks: exponential backoff with jitter, up to 3 attempts.
2. OCR GPU tasks: 2 GPU retries, then 1 CPU retry.
3. External compliance adapters: retry for transient failures, then mark check `pending`.
4. LLM calls: single retry only; avoid repeated expensive retries.
5. All retries must preserve the same `trace_id` and append attempt metadata.

### 10.3 Dead-letter queue handling

1. Any task failing after max retries publishes to `pipeline.dlq`.
2. DLQ payload includes case ID, document ID, step, version, error class, stack summary, and artifact refs.
3. DLQ cases create an operations incident and a human review task automatically.
4. Replay from DLQ is explicit and versioned; no silent auto-replay after code changes.

### 10.4 Safe degradation modes

### Partial extraction mode

Return only high-confidence extracted fields and explicitly mark remaining fields as unresolved.

### Rule-only mode

Disable LLM branch and retrieval branch when those services are degraded; continue deterministic validation and route more cases to review.

### Manual-only mode

If OCR, validation, or compliance dependencies are materially degraded, intake continues, but all cases route to manual review with the pipeline status visibly degraded.

## 11. Human-in-the-Loop Insertion Points

### 11.1 Mandatory human insertion points

1. Intake exception handling
   for unreadable, corrupted, duplicate, unsupported, or quarantined documents.
2. Extraction ambiguity handling
   for missing mandatory fields, conflicting values, or low-confidence critical fields.
3. Validation exception handling
   for freshness failures, major variance, cross-document mismatch, and unresolved ownership issues.
4. Compliance review
   for sanctions, PEP, AML, discrepancy, policy-exception, and pending-critical-check states.
5. Fraud review
   for tampering, suspicious document patterns, anomaly triggers, or identity inconsistency.
6. Final approval or rejection
   for all KYC approvals in MVP, all rejections, all overrides, and all escalated-case dispositions.

### 11.2 Reviewer workstation requirements

The Next.js workstation must include:

1. document viewer with page thumbnails and zoom,
2. OCR text overlay and bounding boxes,
3. field list with confidence, source method, and evidence refs,
4. side-by-side original vs normalized values,
5. rule result panel with severity and reason codes,
6. compliance control panel showing pass / fail / pending / review-required,
7. audit trace viewer,
8. correction form with mandatory reason codes,
9. approval / reject / escalate actions with role enforcement,
10. model/prompt/rule version panel for the current case.

### 11.3 Review action rules

1. Reviewer corrections must create a new human-confirmed layer and must not erase original machine outputs.
2. Any corrected critical field must trigger revalidation before final disposition.
3. Reviewers may perform only the actions allowed by role and workflow policy.
4. Human review remains the default safe path whenever confidence, control status, or evidence completeness is inadequate.

## 12. Structured Output Policy

### 12.1 Output rules

1. All agent outputs must be JSON-only.
2. Every output must include:
   `trace_id`, `case_id`, `document_id` when applicable, `agent_version`, `status`, and timestamp.
3. Critical outputs must also include:
   confidence, rationale, reason codes, and `evidence_refs`.
4. Missing data must be represented explicitly as null, unresolved-field arrays, or error objects.
5. No agent may emit a final approval, rejection, or compliance-clear result outside its allowed boundary.

### 12.2 Evidence requirements

1. Classification output must provide the basis for class assignment.
2. Extraction output must provide field-level evidence refs for all populated required fields.
3. Validation output must provide rule ids, severity, result, and impacted field refs.
4. Compliance output must provide control ids, statuses, and any external reference ids.
5. Decision output must provide route, rationale, and gating factors.

### 12.3 Critical-output minimum contract

For any output that can affect routing, review creation, escalation, or final decision recommendation, the minimum payload is:

1. `status`
2. `reason_codes`
3. `confidence_score`
4. `requires_human_review`
5. `evidence_refs`
6. `version_refs`

## 13. Agent Observability and Logging Requirements

### 13.1 Metrics

### Pipeline metrics

1. documents ingested per hour
2. documents by workflow type
3. queue depth per workflow and agent
4. end-to-end latency p50 / p95 / p99
5. agent latency by service

### Quality metrics

1. VietOCR page confidence distribution
2. OCR corrected-character rate from human review
3. classification accuracy by document type
4. field extraction accuracy by field and document type
5. validation false-pass and false-fail rate
6. human intervention rate
7. escalation rate
8. override rate

### Reliability metrics

1. retry count by agent
2. DLQ count by agent
3. GPU utilization and OCR throughput
4. Temporal workflow failures
5. external dependency availability

### 13.2 Logs

Log these as structured JSON:

1. trace and correlation IDs,
2. agent input/output references,
3. decision rationale,
4. rule execution results,
5. prompt ID + prompt version + response artifact ref for LLM calls,
6. confidence values,
7. reviewer actions,
8. model and feature versions.

For LLM prompt/response logging:

1. store the full prompt and full response in encrypted S3 evidence storage,
2. store redacted metadata in ELK,
3. limit access to full content by compliance and platform roles only.

### 13.3 Alerts

1. OCR confidence drop > configured threshold over rolling 30-minute window
2. extraction accuracy drift by document type
3. spike in `review_required` or `pipeline.dlq`
4. sanctions adapter unavailable
5. abnormal increase in overrides by reviewer or workflow
6. sudden latency increase in VietOCR workers

## 14. Model and Prompt Versioning

### 14.1 Versioning strategy

| Artifact | Version key | Storage |
|---|---|---|
| VietOCR model | `ocr_model_version` | model registry + S3 |
| OpenCV preprocess profile | `preprocess_profile_version` | code repo + PostgreSQL |
| Classification model | `clf_model_version` | model registry + S3 |
| Extraction rules/schema | `schema_version` | Git + PostgreSQL |
| Validation rules | `rule_pack_version` | Git + PostgreSQL |
| LLM prompt | `prompt_template_version` | Git + PostgreSQL |
| Embedding model | `embedding_model_version` | model registry |

Every case artifact must persist the exact versions used.

### 14.2 A/B testing pipeline

1. Run new OCR / classifier / extraction versions in shadow mode first.
2. Compare:
   - field accuracy,
   - critical error rate,
   - human correction rate,
   - latency,
   - escalation impact.
3. Do not let experimental versions make final routing decisions without explicit release approval.
4. Use canary rollout by workflow and document type before broad rollout.

### 14.3 Rollback

1. Keep previous approved model and prompt versions deployable at all times.
2. Decision service reads active versions from a version registry table.
3. Rollback is a config change plus worker cache invalidation, not a code redeploy requirement.
4. Any rollback action is itself an audit event.

## 15. MVP Workflow

1. Use the minimum conservative chain:
   Ingestion -> OCR -> Layout -> Classification -> Extraction -> Validation -> Compliance -> Decision -> Human Review when required -> Audit.
2. Keep deterministic extraction and validation as the default path.
3. Keep LLM fallback off by default unless the document type and field set are explicitly approved for bounded fallback.
4. Restrict straight-through processing to low-risk, policy-approved operational routes only.
5. Require human approval for all KYC approvals and all high-risk or exception cases.

## 16. Scale-Stage Workflow Extensions

1. Add shadow or challenger classification and extraction agents without changing the core contract shape.
2. Add issuer-specific reconciliation sub-agents for difficult statement and payslip templates.
3. Add retrieval-assisted bounded extraction for broader document libraries after benchmark coverage exists.
4. Add advanced fraud-support and entity-linking agents only after specialist review flows and audit coverage are mature.
5. Keep conservative routing unchanged:
   more automation may reduce manual effort, but uncertain or high-risk cases still route to human review.

## 17. Tech Stack Justification

| Layer | Chosen stack | Why this fits banking-grade ops |
|---|---|---|
| Backend | Python + FastAPI | Strong AI ecosystem, fast delivery, typed APIs, good service separation |
| API gateway | Kong or Nginx | Standard ingress, auth, routing, throttling |
| Async tasks | Celery + Kafka | Celery handles worker execution; Kafka provides durable event streams |
| OCR | VietOCR + PyTorch + OpenCV | Mandatory OCR engine, GPU-capable, controllable preprocessing pipeline |
| Workflow | Temporal | Durable workflow execution, retries, timers, signals, human task waits |
| Metadata DB | PostgreSQL | Strong transactional guarantees and relational audit data |
| Object storage | S3 / MinIO | Immutable artifact storage and lifecycle policies |
| Search | OpenSearch | Fast audit/event search and reviewer lookup |
| Vector DB | Weaviate | metadata filtering + semantic retrieval for template and prompt context |
| Classical ML | LightGBM / XGBoost | Fast inference, calibrated probabilities, explainable enough for ops scoring |
| LLM | local Mistral / Llama with OpenAI optional | local-first for data control; external provider optional behind policy gate |
| Frontend | React / Next.js | modern review workstation, good document tooling integration |
| Observability | ELK + Prometheus/Grafana + OpenTelemetry | standard production monitoring and traceability |
| Security | Keycloak, TLS, AES-256 | strong RBAC, encrypted transit and storage |

## 18. Trade-off Analysis

### 18.1 Temporal + Kafka + Celery

### Rationale

Use Temporal for business workflow durability, Kafka for event fan-out, Celery for task execution.

### Trade-off

1. More components to operate.
2. Clearer separation between orchestration and compute.
3. Better than Celery-only orchestration for human review pauses and replayability.

### 18.2 VietOCR as single OCR backbone

### Rationale

Single OCR engine reduces drift, simplifies benchmarking, and satisfies platform constraint.

### Trade-off

1. Fewer fallback OCR options.
2. Requires strong preprocessing and region re-OCR strategy.
3. Operationally acceptable because fallback is human review, not unchecked OCR substitution.

### 18.3 Rules-first architecture

### Rationale

Banking workflows need reproducibility and explainability.

### Trade-off

1. Higher template engineering effort.
2. Lower hallucination risk and easier audit defense.

### 18.4 Local LLM default with optional OpenAI

### Rationale

Banking deployments often need stricter data boundary control.

### Trade-off

1. Local LLM may have lower reasoning quality than top external models.
2. OpenAI optional path can be enabled only with approved data-handling policy.
3. Keeps architecture modular and policy-driven.

## 19. Recommended Build Sequence

1. Foundation: case service, audit service, S3/PostgreSQL/OpenSearch, Keycloak, Kong
2. Temporal workflows + Kafka + Celery worker fabric
3. OCR service with VietOCR and OpenCV preprocessing profiles
4. Layout + deterministic extraction for passport, ID, utility bill, payslip, statement
5. Validation and compliance rule engine
6. Decision service and human review UI
7. Classical ML classifier and anomaly scorers
8. Bounded LLM fallback service
9. A/B testing, drift monitoring, and rollback tooling

This sequence prioritizes banking-grade reliability over model sophistication.

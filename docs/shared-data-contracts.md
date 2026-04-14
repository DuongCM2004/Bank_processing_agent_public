# Shared Data Contracts and JSON Schemas for Ops Agent

## Role

Data Architect and AI Systems Engineer for a banking-grade Document Processing Agent.

## Objective

Define the structured payloads used between services and agents so contracts are explicit, consistent, confidence-aware, evidence-aware, and directly implementable.

## Assumptions

1. These schemas are the shared communication contracts between backend services, AI agents, review flows, and audit components.
2. Payloads must support both synchronous APIs and asynchronous workflow or job orchestration.
3. All critical outputs must support evidence traceability, confidence reporting, and version tracking.
4. JSON payloads should remain implementation-ready for Pydantic, JSON Schema, or TypeScript type generation.
5. Large artifacts such as full OCR blocks or prompt transcripts may be referenced by artifact ids or object keys instead of being fully embedded in every payload.

## Deliverables

- Case schema
- Document metadata schema
- OCR output schema
- Parsing output schema
- Classification output schema
- Extraction output schema
- Validation output schema
- Risk / compliance output schema
- Decision output schema
- Audit event schema
- Human review action schema
- Error schema

## Dependencies

1. [api-specification.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\api-specification.md)
2. [database-persistence-schema.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\database-persistence-schema.md)
3. [ai-architecture.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ai-architecture.md)
4. [prompt-system.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\prompt-system.md)

## 1. Contract Design Rules

1. Every contract uses explicit field names and stable enums.
2. Required fields are listed explicitly per schema.
3. Optional fields must be nullable or omitted consistently.
4. Critical result schemas must include:
   `trace_id`, `status`, `confidence`, `reason_codes`, and `evidence_refs` where applicable.
5. Machine-produced payloads must include version metadata for rules, models, prompts, or schema versions when relevant.
6. IDs are opaque strings with stable prefixes such as `case_`, `doc_`, `artifact_`, `task_`, `audit_`.

## 2. Shared Primitive Schemas

### 2.1 Common envelope

Used for all internal agent or service contracts.

Required fields:

1. `trace_id`
2. `timestamp_utc`
3. `schema_version`

Optional fields:

1. `case_id`
2. `document_id`
3. `workflow_run_id`
4. `producer_service`
5. `producer_version`

Example:

```json
{
  "trace_id": "trc_123",
  "timestamp_utc": "2026-04-14T11:00:00Z",
  "schema_version": "1.0.0",
  "case_id": "case_123",
  "document_id": "doc_123",
  "workflow_run_id": "wf_123",
  "producer_service": "extraction_service",
  "producer_version": "1.2.0"
}
```

### 2.2 Confidence schema

Required fields:

1. `score`
2. `label`

Optional fields:

1. `method`
2. `contributors`

```json
{
  "score": 0.93,
  "label": "medium_confidence",
  "method": "weighted_field_aggregate",
  "contributors": {
    "ocr_confidence": 0.95,
    "anchor_match_score": 0.90
  }
}
```

Allowed labels:

1. `high_confidence`
2. `medium_confidence`
3. `low_confidence`
4. `not_confident`

### 2.3 Evidence reference schema

Required fields:

1. `document_id`

Optional fields:

1. `document_version_id`
2. `artifact_id`
3. `page_number`
4. `text_span`
5. `bbox`
6. `evidence_rank`

```json
{
  "document_id": "doc_123",
  "document_version_id": "docver_001",
  "artifact_id": "artifact_ocr_001",
  "page_number": 1,
  "text_span": "NGUYEN VAN A",
  "bbox": {
    "x": 0.12,
    "y": 0.18,
    "width": 0.42,
    "height": 0.07
  },
  "evidence_rank": 1
}
```

### 2.4 Version reference schema

Optional fields, included when relevant:

1. `workflow_definition_version`
2. `schema_version`
3. `rule_pack_version`
4. `ocr_model_version`
5. `classifier_model_version`
6. `prompt_version`
7. `preprocess_profile_version`

## 3. Case Schema

### Purpose

Represents one operational workflow case for API retrieval and orchestration.

Required fields:

1. `case_id`
2. `workflow_type`
3. `priority`
4. `status`
5. `review_required`
6. `assigned_queue`
7. `created_at_utc`
8. `updated_at_utc`

Optional fields:

1. `customer_reference`
2. `compliance_status`
3. `final_outcome`
4. `document_ids`
5. `review_task_ids`
6. `current_workflow_run_id`
7. `version_refs`

```json
{
  "case_id": "case_123",
  "workflow_type": "kyc_onboarding",
  "priority": "normal",
  "status": "review_required",
  "review_required": true,
  "assigned_queue": "ops_review",
  "created_at_utc": "2026-04-14T11:00:00Z",
  "updated_at_utc": "2026-04-14T11:00:00Z",
  "customer_reference": "cust_001",
  "compliance_status": "pending",
  "final_outcome": null,
  "document_ids": ["doc_123"],
  "review_task_ids": ["task_123"],
  "current_workflow_run_id": "wf_123",
  "version_refs": {
    "workflow_definition_version": "1.0.0"
  }
}
```

## 4. Document Metadata Schema

### Purpose

Represents document registration and current processing metadata.

Required fields:

1. `document_id`
2. `case_id`
3. `filename`
4. `mime_type`
5. `source_channel`
6. `retention_class`
7. `status`
8. `created_at_utc`

Optional fields:

1. `document_role`
2. `document_version_id`
3. `file_hash`
4. `raw_object_key`
5. `page_count`
6. `quarantine_status`

```json
{
  "document_id": "doc_123",
  "case_id": "case_123",
  "filename": "passport.pdf",
  "mime_type": "application/pdf",
  "source_channel": "manual_upload",
  "retention_class": "bank_ops_default",
  "status": "processing",
  "created_at_utc": "2026-04-14T11:00:00Z",
  "document_role": "id_document",
  "document_version_id": "docver_001",
  "file_hash": "sha256hex",
  "raw_object_key": "raw/2026/04/14/case_123/doc_123/original.pdf",
  "page_count": 2,
  "quarantine_status": "accepted"
}
```

## 5. OCR Output Schema

### Purpose

Represents OCR result summary plus references to detailed OCR artifacts.

Required fields:

1. `trace_id`
2. `case_id`
3. `document_id`
4. `ocr_result_id`
5. `status`
6. `confidence`
7. `artifact_id`
8. `page_count`
9. `version_refs`

Optional fields:

1. `document_version_id`
2. `pages`
3. `errors`

Page object required fields:

1. `page_number`
2. `page_confidence`
3. `coverage_ratio`
4. `image_quality_score`

Optional page fields:

1. `text_blocks_ref`
2. `preview_object_key`

```json
{
  "trace_id": "trc_ocr_001",
  "case_id": "case_123",
  "document_id": "doc_123",
  "ocr_result_id": "ocr_001",
  "status": "completed",
  "confidence": {
    "score": 0.947,
    "label": "high_confidence",
    "method": "weighted_page_aggregate"
  },
  "artifact_id": "artifact_ocr_001",
  "page_count": 2,
  "version_refs": {
    "ocr_model_version": "vietocr-bank-v3",
    "preprocess_profile_version": "deskew_denoise_v1"
  },
  "pages": [
    {
      "page_number": 1,
      "page_confidence": 0.952,
      "coverage_ratio": 0.96,
      "image_quality_score": 0.91,
      "text_blocks_ref": "artifact_ocr_001#page_1"
    }
  ],
  "errors": []
}
```

## 6. Parsing Output Schema

### Purpose

Represents layout or structure parsing output for a document.

Required fields:

1. `trace_id`
2. `case_id`
3. `document_id`
4. `layout_result_id`
5. `status`
6. `artifact_id`
7. `regions`
8. `confidence`
9. `version_refs`

Region required fields:

1. `region_id`
2. `region_type`
3. `page_number`
4. `bbox`

Optional region fields:

1. `confidence`
2. `linked_ocr_block_refs`

```json
{
  "trace_id": "trc_layout_001",
  "case_id": "case_123",
  "document_id": "doc_123",
  "layout_result_id": "layout_001",
  "status": "completed",
  "artifact_id": "artifact_layout_001",
  "confidence": {
    "score": 0.91,
    "label": "medium_confidence",
    "method": "geometric_consistency"
  },
  "version_refs": {
    "schema_version": "1.0.0",
    "producer_version": "layout_service_v1"
  },
  "regions": [
    {
      "region_id": "region_001",
      "region_type": "key_value_zone",
      "page_number": 1,
      "bbox": {
        "x": 0.08,
        "y": 0.15,
        "width": 0.84,
        "height": 0.22
      },
      "confidence": {
        "score": 0.89,
        "label": "medium_confidence"
      },
      "linked_ocr_block_refs": ["artifact_ocr_001#blk_7"]
    }
  ]
}
```

## 7. Classification Output Schema

### Purpose

Represents document-type prediction and candidate class ranking.

Required fields:

1. `trace_id`
2. `case_id`
3. `document_id`
4. `classification_result_id`
5. `document_type`
6. `confidence`
7. `candidate_types`
8. `status`
9. `reason_codes`
10. `version_refs`

Candidate type required fields:

1. `label`
2. `score`

Optional fields:

1. `subtype`
2. `requires_human_review`
3. `evidence_refs`

```json
{
  "trace_id": "trc_clf_001",
  "case_id": "case_123",
  "document_id": "doc_123",
  "classification_result_id": "clf_001",
  "document_type": "passport",
  "subtype": "standard_passport",
  "confidence": {
    "score": 0.962,
    "label": "high_confidence",
    "method": "calibrated_model_probability"
  },
  "candidate_types": [
    {
      "label": "passport",
      "score": 0.962
    },
    {
      "label": "national_id",
      "score": 0.021
    }
  ],
  "status": "completed",
  "reason_codes": [],
  "requires_human_review": false,
  "evidence_refs": [
    {
      "document_id": "doc_123",
      "artifact_id": "artifact_ocr_001",
      "page_number": 1,
      "text_span": "PASSPORT"
    }
  ],
  "version_refs": {
    "classifier_model_version": "clf-v2.1"
  }
}
```

## 8. Extraction Output Schema

### Purpose

Represents extracted fields, missing fields, conflicts, and extraction confidence.

Required fields:

1. `trace_id`
2. `case_id`
3. `document_id`
4. `extraction_run_id`
5. `document_type`
6. `schema_name`
7. `status`
8. `confidence`
9. `fields`
10. `missing_fields`
11. `conflicts`
12. `reason_codes`
13. `version_refs`

Field required fields:

1. `field_name`
2. `required`
3. `status`

Optional field fields:

1. `value`
2. `normalized_value`
3. `value_type`
4. `confidence`
5. `method`
6. `reason_code`
7. `evidence_refs`

Conflict required fields:

1. `field_name`
2. `candidate_values`
3. `reason_code`

```json
{
  "trace_id": "trc_ext_001",
  "case_id": "case_123",
  "document_id": "doc_123",
  "extraction_run_id": "ext_001",
  "document_type": "passport",
  "schema_name": "passport_v1",
  "status": "completed",
  "confidence": {
    "score": 0.968,
    "label": "high_confidence",
    "method": "critical_field_min_plus_weighted_mean"
  },
  "fields": [
    {
      "field_name": "full_name",
      "value": "NGUYEN VAN A",
      "normalized_value": "NGUYEN VAN A",
      "value_type": "string",
      "required": true,
      "status": "extracted",
      "confidence": {
        "score": 0.97,
        "label": "high_confidence",
        "method": "anchor_plus_ocr"
      },
      "method": "rule_anchor",
      "reason_code": null,
      "evidence_refs": [
        {
          "document_id": "doc_123",
          "document_version_id": "docver_001",
          "artifact_id": "artifact_ocr_001",
          "page_number": 1,
          "text_span": "NGUYEN VAN A"
        }
      ]
    }
  ],
  "missing_fields": [],
  "conflicts": [],
  "reason_codes": [],
  "version_refs": {
    "schema_version": "passport_v1",
    "ocr_model_version": "vietocr-bank-v3",
    "prompt_version": null
  }
}
```

## 9. Validation Output Schema

### Purpose

Represents rule-based validation outcomes at document or case level.

Required fields:

1. `trace_id`
2. `case_id`
3. `validation_run_id`
4. `status`
5. `results`
6. `confidence`
7. `version_refs`

Optional fields:

1. `document_id`
2. `blocking_issue_count`
3. `warning_count`

Validation result required fields:

1. `rule_id`
2. `rule_version`
3. `result`
4. `severity`
5. `reason_code`

Optional validation result fields:

1. `impacted_field_name`
2. `details`
3. `evidence_refs`

```json
{
  "trace_id": "trc_val_001",
  "case_id": "case_123",
  "document_id": "doc_123",
  "validation_run_id": "val_001",
  "status": "completed",
  "confidence": {
    "score": 0.979,
    "label": "high_confidence",
    "method": "rule_pass_ratio_weighted_by_criticality"
  },
  "blocking_issue_count": 0,
  "warning_count": 1,
  "results": [
    {
      "rule_id": "kyc.id.expiry_valid",
      "rule_version": "1.0.0",
      "result": "pass",
      "severity": "info",
      "reason_code": "valid_document",
      "impacted_field_name": "expiry_date",
      "details": {},
      "evidence_refs": [
        {
          "document_id": "doc_123",
          "page_number": 1,
          "text_span": "2030-04-10"
        }
      ]
    }
  ],
  "version_refs": {
    "rule_pack_version": "rules-1.0.0",
    "schema_version": "passport_v1"
  }
}
```

## 10. Risk / Compliance Output Schema

### Purpose

Represents compliance control status and escalation triggers.

Required fields:

1. `trace_id`
2. `case_id`
3. `compliance_evaluation_id`
4. `compliance_status`
5. `status`
6. `control_results`
7. `requires_human_review`
8. `escalation_recommendation`
9. `reason_codes`
10. `version_refs`

Control result required fields:

1. `control_id`
2. `status`

Optional control result fields:

1. `severity`
2. `reason_code`
3. `external_ref`
4. `evidence_refs`

Allowed `compliance_status` values:

1. `pending`
2. `completed_pass`
3. `completed_fail`
4. `review_required`
5. `partial_compliance`
6. `non_compliant`

```json
{
  "trace_id": "trc_comp_001",
  "case_id": "case_123",
  "compliance_evaluation_id": "comp_001",
  "compliance_status": "partial_compliance",
  "status": "completed",
  "requires_human_review": true,
  "escalation_recommendation": "compliance_review",
  "reason_codes": ["pending_critical_check"],
  "control_results": [
    {
      "control_id": "CCM-04",
      "status": "pending",
      "severity": "critical",
      "reason_code": "sanctions_check_pending",
      "external_ref": "screening_req_001",
      "evidence_refs": []
    }
  ],
  "version_refs": {
    "rule_pack_version": "controls-1.0.0"
  }
}
```

## 11. Decision Output Schema

### Purpose

Represents the next route selected by workflow policy.

Required fields:

1. `trace_id`
2. `case_id`
3. `decision_run_id`
4. `route`
5. `decision_type`
6. `status`
7. `confidence`
8. `requires_human_review`
9. `reason_codes`
10. `version_refs`

Optional fields:

1. `next_action`
2. `rationale`
3. `evidence_refs`
4. `pending_critical_checks`

Allowed `route` values:

1. `auto_process`
2. `cross_check`
3. `human_review`
4. `specialist_escalation`
5. `manual_intake_resolution`

```json
{
  "trace_id": "trc_dec_001",
  "case_id": "case_123",
  "decision_run_id": "dec_001",
  "route": "human_review",
  "decision_type": "review_required",
  "status": "completed",
  "confidence": {
    "score": 0.0,
    "label": "not_confident",
    "method": "hard_gate_due_to_pending_critical_check"
  },
  "requires_human_review": true,
  "reason_codes": ["pending_critical_check", "human_review_required_for_kyc_release"],
  "next_action": "create_review_task",
  "rationale": [
    "pending_critical_check:CCM-04",
    "human_review_required_for_kyc_release"
  ],
  "evidence_refs": [],
  "pending_critical_checks": ["CCM-04"],
  "version_refs": {
    "rule_pack_version": "decision-rules-1.0.0"
  }
}
```

## 12. Audit Event Schema

### Purpose

Represents an immutable, append-only audit record.

Required fields:

1. `event_id`
2. `trace_id`
3. `case_id`
4. `resource_type`
5. `resource_id`
6. `action`
7. `actor_type`
8. `actor_id`
9. `occurred_at_utc`

Optional fields:

1. `details`
2. `immutable_hash`
3. `version_refs`

```json
{
  "event_id": "audit_123",
  "trace_id": "trc_123",
  "case_id": "case_123",
  "resource_type": "case",
  "resource_id": "case_123",
  "action": "case_state_changed",
  "actor_type": "user",
  "actor_id": "reviewer_007",
  "occurred_at_utc": "2026-04-14T11:25:00Z",
  "details": {
    "from_status": "in_review",
    "to_status": "corrected",
    "reason_code": "field_corrections_recorded"
  },
  "immutable_hash": "hex"
}
```

## 13. Human Review Action Schema

### Purpose

Represents a manual review action that changes or advances the workflow.

Required fields:

1. `review_action_id`
2. `case_id`
3. `action_type`
4. `actor_id`
5. `reason_code`
6. `created_at_utc`

Optional fields:

1. `review_task_id`
2. `comment`
3. `payload`
4. `evidence_refs`
5. `trace_id`

Allowed `action_type` values:

1. `claim`
2. `correct_field`
3. `escalate`
4. `revalidate`
5. `close`
6. `comment`

```json
{
  "review_action_id": "ract_001",
  "case_id": "case_123",
  "review_task_id": "task_123",
  "action_type": "correct_field",
  "actor_id": "reviewer_007",
  "reason_code": "reviewer_confirmed_typo",
  "comment": "OCR dropped trailing character",
  "payload": {
    "field_name": "full_name",
    "new_value": "NGUYEN VAN AN"
  },
  "evidence_refs": [
    {
      "document_id": "doc_123",
      "page_number": 1,
      "text_span": "NGUYEN VAN AN"
    }
  ],
  "trace_id": "trc_review_001",
  "created_at_utc": "2026-04-14T11:24:00Z"
}
```

## 14. Error Schema

### Purpose

Represents a standard machine-readable failure response across APIs and internal workflows.

Required fields:

1. `error_code`
2. `message`
3. `trace_id`
4. `retryable`

Optional fields:

1. `details`
2. `status_code`
3. `failing_step`
4. `artifact_refs`

```json
{
  "error_code": "invalid_state_transition",
  "message": "Cannot transition case case_123 from review_required to closed.",
  "trace_id": "trc_err_001",
  "retryable": false,
  "status_code": 409,
  "failing_step": "close_case",
  "details": {
    "case_id": "case_123",
    "from_status": "review_required",
    "requested_status": "closed"
  },
  "artifact_refs": []
}
```

## 15. Contract Implementation Guidance

1. Prefer generating Pydantic models and TypeScript types from a single schema source.
2. Keep enum values centralized and versioned.
3. Use `jsonb` storage for flexible `details`, `payload`, `candidate_types`, and `contributors`, but keep core routing fields normalized.
4. Reject payloads that omit required fields or use unknown enum values.
5. Do not omit critical review or confidence flags just because the producing service lacks certainty; express uncertainty explicitly.

## 16. Recommended Contract Stance

The shared contracts should remain:

1. strict enough for workflow safety,
2. explicit enough for audit and evidence traceability,
3. compact enough for service-to-service communication,
4. versioned enough for replay and rollback,
5. consistent across API, orchestration, and agent layers.

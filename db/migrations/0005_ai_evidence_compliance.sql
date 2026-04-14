BEGIN;

CREATE TABLE IF NOT EXISTS ops_ai.ocr_runs (
    ocr_run_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    document_id TEXT NOT NULL REFERENCES ops_core.documents(document_id),
    document_version_id TEXT NOT NULL,
    source_artifact_id TEXT NULL REFERENCES ops_ai.artifacts(artifact_id),
    output_artifact_id TEXT NULL REFERENCES ops_ai.artifacts(artifact_id),
    model_version TEXT NOT NULL,
    preprocess_profile_version TEXT NULL,
    status TEXT NOT NULL,
    overall_confidence NUMERIC(5,4) NULL,
    page_count INTEGER NOT NULL DEFAULT 0,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_ai.ocr_page_results (
    ocr_page_result_id TEXT PRIMARY KEY,
    ocr_run_id TEXT NOT NULL REFERENCES ops_ai.ocr_runs(ocr_run_id),
    document_page_id TEXT NOT NULL REFERENCES ops_core.document_pages(document_page_id),
    page_number INTEGER NOT NULL,
    confidence_score NUMERIC(5,4) NULL,
    coverage_ratio NUMERIC(5,4) NULL,
    image_quality_score NUMERIC(5,4) NULL,
    text_blocks_artifact_ref TEXT NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (ocr_run_id, page_number)
);

CREATE TABLE IF NOT EXISTS ops_ai.classification_runs (
    classification_run_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    document_id TEXT NOT NULL REFERENCES ops_core.documents(document_id),
    document_version_id TEXT NOT NULL,
    classifier_model_version TEXT NOT NULL,
    status TEXT NOT NULL,
    document_type TEXT NOT NULL,
    document_subtype TEXT NULL,
    confidence_score NUMERIC(5,4) NULL,
    requires_human_review BOOLEAN NOT NULL DEFAULT FALSE,
    candidates_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_ai.field_evidence_refs (
    field_evidence_ref_id TEXT PRIMARY KEY,
    extracted_field_id TEXT NOT NULL REFERENCES ops_ai.extracted_fields(extracted_field_id),
    document_id TEXT NOT NULL REFERENCES ops_core.documents(document_id),
    document_version_id TEXT NOT NULL,
    document_page_id TEXT NULL REFERENCES ops_core.document_pages(document_page_id),
    artifact_id TEXT NULL REFERENCES ops_ai.artifacts(artifact_id),
    page_number INTEGER NULL,
    text_span TEXT NULL,
    bbox_json JSONB NULL,
    evidence_rank INTEGER NOT NULL DEFAULT 1,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_rules.validation_evidence_refs (
    validation_evidence_ref_id TEXT PRIMARY KEY,
    validation_result_id TEXT NOT NULL REFERENCES ops_rules.validation_results(validation_result_id),
    document_id TEXT NULL REFERENCES ops_core.documents(document_id),
    document_page_id TEXT NULL REFERENCES ops_core.document_pages(document_page_id),
    artifact_id TEXT NULL REFERENCES ops_ai.artifacts(artifact_id),
    page_number INTEGER NULL,
    text_span TEXT NULL,
    bbox_json JSONB NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_rules.compliance_evaluations (
    compliance_evaluation_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    workflow_run_id TEXT NULL REFERENCES ops_core.workflow_runs(workflow_run_id),
    status TEXT NOT NULL,
    compliance_status TEXT NOT NULL,
    rule_pack_version TEXT NOT NULL,
    requires_human_review BOOLEAN NOT NULL DEFAULT FALSE,
    escalation_recommendation TEXT NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_rules.compliance_control_results (
    compliance_control_result_id TEXT PRIMARY KEY,
    compliance_evaluation_id TEXT NOT NULL REFERENCES ops_rules.compliance_evaluations(compliance_evaluation_id),
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    control_id TEXT NOT NULL,
    control_version TEXT NOT NULL,
    status TEXT NOT NULL,
    severity TEXT NULL,
    reason_code TEXT NULL,
    external_ref TEXT NULL,
    details_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_rules.risk_findings (
    risk_finding_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    document_id TEXT NULL REFERENCES ops_core.documents(document_id),
    workflow_run_id TEXT NULL REFERENCES ops_core.workflow_runs(workflow_run_id),
    finding_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    status TEXT NOT NULL,
    summary TEXT NOT NULL,
    evidence_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_rules.decision_inputs (
    decision_input_id TEXT PRIMARY KEY,
    decision_run_id TEXT NOT NULL REFERENCES ops_rules.decision_runs(decision_run_id),
    ocr_confidence NUMERIC(5,4) NULL,
    classification_confidence NUMERIC(5,4) NULL,
    extraction_confidence NUMERIC(5,4) NULL,
    validation_confidence NUMERIC(5,4) NULL,
    compliance_status TEXT NOT NULL,
    critical_failures_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    pending_critical_checks_json JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS ops_review.review_action_evidence_refs (
    review_action_evidence_ref_id TEXT PRIMARY KEY,
    review_action_id TEXT NOT NULL REFERENCES ops_review.review_actions(review_action_id),
    document_id TEXT NOT NULL REFERENCES ops_core.documents(document_id),
    document_version_id TEXT NOT NULL,
    document_page_id TEXT NULL REFERENCES ops_core.document_pages(document_page_id),
    artifact_id TEXT NULL REFERENCES ops_ai.artifacts(artifact_id),
    page_number INTEGER NULL,
    text_span TEXT NULL,
    bbox_json JSONB NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ocr_runs_document_id ON ops_ai.ocr_runs (document_id, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_classification_runs_document_id ON ops_ai.classification_runs (document_id, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_field_evidence_refs_extracted_field_id ON ops_ai.field_evidence_refs (extracted_field_id, evidence_rank);
CREATE INDEX IF NOT EXISTS idx_validation_evidence_refs_validation_result_id ON ops_rules.validation_evidence_refs (validation_result_id);
CREATE INDEX IF NOT EXISTS idx_compliance_evaluations_case_id ON ops_rules.compliance_evaluations (case_id, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_compliance_control_results_case_id ON ops_rules.compliance_control_results (case_id, control_id, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_risk_findings_case_id ON ops_rules.risk_findings (case_id, severity, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_review_action_evidence_refs_review_action_id ON ops_review.review_action_evidence_refs (review_action_id);

COMMIT;

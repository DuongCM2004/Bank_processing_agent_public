BEGIN;

CREATE TABLE IF NOT EXISTS ops_ai.artifacts (
    artifact_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    document_id TEXT NULL REFERENCES ops_core.documents(document_id),
    document_version_id TEXT NULL,
    artifact_type TEXT NOT NULL,
    object_key TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    producer_service TEXT NOT NULL,
    producer_version TEXT NOT NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_ai.extraction_runs (
    extraction_run_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    document_id TEXT NOT NULL REFERENCES ops_core.documents(document_id),
    document_version_id TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    method TEXT NOT NULL,
    prompt_version TEXT NULL,
    model_version TEXT NULL,
    status TEXT NOT NULL,
    extraction_confidence NUMERIC(5,4) NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_ai.extracted_fields (
    extracted_field_id TEXT PRIMARY KEY,
    extraction_run_id TEXT NOT NULL REFERENCES ops_ai.extraction_runs(extraction_run_id),
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    document_id TEXT NOT NULL REFERENCES ops_core.documents(document_id),
    document_version_id TEXT NOT NULL,
    field_name TEXT NOT NULL,
    field_value TEXT NULL,
    normalized_value TEXT NULL,
    value_type TEXT NULL,
    required_flag BOOLEAN NOT NULL,
    confidence_score NUMERIC(5,4) NULL,
    confidence_label TEXT NULL,
    method TEXT NOT NULL,
    status TEXT NOT NULL,
    reason_code TEXT NULL,
    reviewed_by_human BOOLEAN NOT NULL DEFAULT FALSE,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_rules.validation_runs (
    validation_run_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    document_id TEXT NULL REFERENCES ops_core.documents(document_id),
    document_version_id TEXT NULL,
    rule_pack_version TEXT NOT NULL,
    schema_version TEXT NULL,
    status TEXT NOT NULL,
    validation_confidence NUMERIC(5,4) NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_rules.validation_results (
    validation_result_id TEXT PRIMARY KEY,
    validation_run_id TEXT NOT NULL REFERENCES ops_rules.validation_runs(validation_run_id),
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    document_id TEXT NULL REFERENCES ops_core.documents(document_id),
    rule_id TEXT NOT NULL,
    rule_version TEXT NOT NULL,
    severity TEXT NOT NULL,
    result TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    impacted_field_name TEXT NULL,
    details_json JSONB NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_rules.decision_runs (
    decision_run_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    workflow_run_id TEXT NOT NULL REFERENCES ops_core.workflow_runs(workflow_run_id),
    decision_type TEXT NOT NULL,
    route TEXT NOT NULL,
    decision_status TEXT NOT NULL,
    decision_confidence NUMERIC(5,4) NULL,
    rationale_json JSONB NULL,
    requires_human_review BOOLEAN NOT NULL,
    rule_pack_version TEXT NOT NULL,
    prompt_version TEXT NULL,
    model_version TEXT NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_review.review_tasks (
    review_task_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    task_type TEXT NOT NULL,
    status TEXT NOT NULL,
    assigned_queue TEXT NOT NULL,
    assigned_to TEXT NULL,
    priority TEXT NOT NULL,
    reason_codes_json JSONB NOT NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    claimed_at_utc TIMESTAMPTZ NULL,
    completed_at_utc TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS ops_review.review_actions (
    review_action_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    review_task_id TEXT NULL REFERENCES ops_review.review_tasks(review_task_id),
    action_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    comment TEXT NULL,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    trace_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ops_audit.audit_events (
    event_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    action TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    occurred_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    details_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    immutable_hash TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_artifacts_document_type ON ops_ai.artifacts (document_version_id, artifact_type, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_extracted_fields_case_field ON ops_ai.extracted_fields (case_id, field_name, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_validation_results_case_id ON ops_rules.validation_results (case_id, severity, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_review_tasks_queue ON ops_review.review_tasks (status, assigned_queue, priority, created_at_utc);
CREATE INDEX IF NOT EXISTS idx_review_actions_case_id ON ops_review.review_actions (case_id, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_case_id ON ops_audit.audit_events (case_id, occurred_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_trace_id ON ops_audit.audit_events (trace_id);

COMMIT;

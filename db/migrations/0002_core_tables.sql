BEGIN;

CREATE TABLE IF NOT EXISTS ops_core.cases (
    case_id TEXT PRIMARY KEY,
    workflow_type TEXT NOT NULL,
    priority TEXT NOT NULL,
    customer_reference TEXT NULL,
    status TEXT NOT NULL,
    compliance_status TEXT NULL,
    assigned_queue TEXT NOT NULL,
    review_required BOOLEAN NOT NULL DEFAULT FALSE,
    final_outcome TEXT NULL,
    current_workflow_run_id TEXT NULL,
    created_by TEXT NOT NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    record_version BIGINT NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS ops_core.case_status_history (
    case_status_event_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    from_status TEXT NULL,
    to_status TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    occurred_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_core.documents (
    document_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    document_role TEXT NULL,
    filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    source_channel TEXT NOT NULL,
    retention_class TEXT NOT NULL,
    status TEXT NOT NULL,
    latest_document_version_id TEXT NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_core.document_versions (
    document_version_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES ops_core.documents(document_id),
    version_no INTEGER NOT NULL,
    raw_object_key TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    byte_size BIGINT NULL,
    page_count INTEGER NULL,
    quarantine_status TEXT NOT NULL,
    supersedes_document_version_id TEXT NULL,
    created_by TEXT NOT NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, version_no)
);

CREATE TABLE IF NOT EXISTS ops_core.workflow_runs (
    workflow_run_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    workflow_engine TEXT NOT NULL DEFAULT 'temporal',
    workflow_definition_version TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at_utc TIMESTAMPTZ NULL,
    trace_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ops_core.workflow_step_runs (
    workflow_step_run_id TEXT PRIMARY KEY,
    workflow_run_id TEXT NOT NULL REFERENCES ops_core.workflow_runs(workflow_run_id),
    case_id TEXT NOT NULL REFERENCES ops_core.cases(case_id),
    document_id TEXT NULL REFERENCES ops_core.documents(document_id),
    step_name TEXT NOT NULL,
    step_version TEXT NOT NULL,
    attempt_no INTEGER NOT NULL,
    status TEXT NOT NULL,
    input_artifact_id TEXT NULL,
    output_artifact_id TEXT NULL,
    error_code TEXT NULL,
    error_message TEXT NULL,
    started_at_utc TIMESTAMPTZ NULL,
    finished_at_utc TIMESTAMPTZ NULL,
    trace_id TEXT NOT NULL,
    UNIQUE (workflow_run_id, document_id, step_name, step_version, attempt_no)
);

CREATE TABLE IF NOT EXISTS ops_core.outbox_events (
    outbox_event_id TEXT PRIMARY KEY,
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    publish_status TEXT NOT NULL DEFAULT 'pending',
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at_utc TIMESTAMPTZ NULL,
    trace_id TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cases_status ON ops_core.cases (workflow_type, status);
CREATE INDEX IF NOT EXISTS idx_cases_queue ON ops_core.cases (assigned_queue, priority, updated_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_documents_case_id ON ops_core.documents (case_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_case_id ON ops_core.workflow_runs (case_id);
CREATE INDEX IF NOT EXISTS idx_workflow_step_runs_case_id ON ops_core.workflow_step_runs (case_id, step_name, status);

COMMIT;

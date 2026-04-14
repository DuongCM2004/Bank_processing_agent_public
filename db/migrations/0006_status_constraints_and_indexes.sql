BEGIN;

ALTER TABLE ops_core.cases
    ADD CONSTRAINT ck_cases_priority
    CHECK (priority IN ('low', 'normal', 'high', 'critical'));

ALTER TABLE ops_core.cases
    ADD CONSTRAINT ck_cases_status
    CHECK (status IN (
        'received',
        'stored',
        'queued',
        'processing',
        'validated',
        'review_required',
        'in_review',
        'corrected',
        'approved',
        'rejected',
        'escalated',
        'failed',
        'closed'
    ));

ALTER TABLE ops_core.case_status_history
    ADD CONSTRAINT ck_case_status_history_from_status
    CHECK (
        from_status IS NULL OR from_status IN (
            'received',
            'stored',
            'queued',
            'processing',
            'validated',
            'review_required',
            'in_review',
            'corrected',
            'approved',
            'rejected',
            'escalated',
            'failed',
            'closed'
        )
    );

ALTER TABLE ops_core.case_status_history
    ADD CONSTRAINT ck_case_status_history_to_status
    CHECK (to_status IN (
        'received',
        'stored',
        'queued',
        'processing',
        'validated',
        'review_required',
        'in_review',
        'corrected',
        'approved',
        'rejected',
        'escalated',
        'failed',
        'closed'
    ));

ALTER TABLE ops_core.documents
    ADD CONSTRAINT ck_documents_status
    CHECK (status IN ('not_started', 'in_progress', 'complete', 'failed'));

ALTER TABLE ops_core.workflow_runs
    ADD CONSTRAINT ck_workflow_runs_status
    CHECK (status IN ('queued', 'in_progress', 'waiting_review', 'completed', 'failed'));

ALTER TABLE ops_core.workflow_step_runs
    ADD CONSTRAINT ck_workflow_step_runs_status
    CHECK (status IN ('pending', 'in_progress', 'completed', 'failed'));

ALTER TABLE ops_core.outbox_events
    ADD CONSTRAINT ck_outbox_events_publish_status
    CHECK (publish_status IN ('pending', 'published', 'failed'));

ALTER TABLE ops_ai.extraction_runs
    ADD CONSTRAINT ck_extraction_runs_status
    CHECK (status IN ('not_started', 'in_progress', 'complete', 'failed'));

ALTER TABLE ops_rules.validation_runs
    ADD CONSTRAINT ck_validation_runs_status
    CHECK (status IN ('not_started', 'in_progress', 'complete', 'failed'));

ALTER TABLE ops_review.review_tasks
    ADD CONSTRAINT ck_review_tasks_status
    CHECK (status IN ('open', 'claimed', 'completed'));

ALTER TABLE ops_review.review_actions
    ADD CONSTRAINT ck_review_actions_action_type
    CHECK (action_type IN ('claim', 'correct_field', 'escalate', 'revalidate', 'close'));

ALTER TABLE ops_audit.audit_events
    ADD CONSTRAINT ck_audit_events_actor_type
    CHECK (actor_type IN ('system', 'user', 'service'));

CREATE INDEX IF NOT EXISTS idx_case_status_history_case_time
    ON ops_core.case_status_history (case_id, occurred_at_utc DESC);

CREATE INDEX IF NOT EXISTS idx_workflow_runs_case_status
    ON ops_core.workflow_runs (case_id, status, started_at_utc DESC);

CREATE INDEX IF NOT EXISTS idx_workflow_step_runs_workflow_step
    ON ops_core.workflow_step_runs (workflow_run_id, step_name, attempt_no DESC);

CREATE INDEX IF NOT EXISTS idx_outbox_events_pending
    ON ops_core.outbox_events (publish_status, created_at_utc)
    WHERE publish_status = 'pending';

CREATE INDEX IF NOT EXISTS idx_extraction_runs_case_document
    ON ops_ai.extraction_runs (case_id, document_id, created_at_utc DESC);

CREATE INDEX IF NOT EXISTS idx_validation_runs_case_document
    ON ops_rules.validation_runs (case_id, document_id, created_at_utc DESC);

CREATE INDEX IF NOT EXISTS idx_review_tasks_assignee_status
    ON ops_review.review_tasks (assigned_to, status, updated_at_utc DESC);

CREATE INDEX IF NOT EXISTS idx_audit_events_resource
    ON ops_audit.audit_events (resource_type, resource_id, occurred_at_utc DESC);

COMMIT;

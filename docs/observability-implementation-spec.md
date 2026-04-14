# Observability Implementation Specification

This specification defines audit logging, operational logging, metrics, dashboards, and alerting for the banking Document Processing Agent (Ops Agent). It distinguishes compliance-grade audit records from engineering-grade operational telemetry and is aligned to [audit_logging.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/audit_logging.py), [observability.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/observability.py), [workflow_contracts.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/workflow_contracts.py), and [audit-event.json](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/contracts/jsonschema/audit-event.json).

## Observability Scope

The MVP observability model has four distinct outputs:

1. immutable audit events
2. structured operational logs
3. metrics
4. traces or trace-aligned correlation ids

Separation rule:

- audit logs are the compliance and evidence trail
- operational logs are for debugging, support, and runtime health
- metrics are for trend and alerting
- traces are for causal path reconstruction across API, workflow, providers, and review actions

## 1. Audit Event Model

The canonical audit contract is [audit-event.json](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/contracts/jsonschema/audit-event.json).

Required audit fields:

- `event_id`
- `trace_id`
- `case_id`
- `resource_type`
- `resource_id`
- `action`
- `actor_type`
- `actor_id`
- `occurred_at_utc`

Recommended audit fields:

- `details`
- `immutable_hash`
- `version_refs`
- `workflow_run_id`
- `document_id`
- `review_task_id`

Audit event rules:

- audit events are append-only
- audit events must reference the relevant case
- audit events must include evidence refs or artifact ids when a machine or reviewer action depended on evidence
- audit events may include safe reasoning summaries, never raw chain-of-thought
- audit events must be emitted on every state transition and reviewer mutation

Audit emission points:

- case created
- document registered
- document version stored
- workflow start command persisted
- workflow run started
- workflow step started/completed/retried/timed_out/failed
- state transition executed
- review task created/claimed/completed
- manual correction submitted
- escalation requested
- revalidation requested/completed
- decision recorded
- closure recorded
- audit write failure detected

## 2. Operational Log Categories

Operational log categories are defined in [observability.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/observability.py).

MVP categories:

- `api_request`
- `auth`
- `case_lifecycle`
- `document_io`
- `workflow`
- `agent_runtime`
- `review`
- `queue`
- `integration`
- `security`
- `audit_pipeline`

Category rules:

- each log event must declare exactly one primary category
- category drives dashboard routing and alert ownership
- do not use `details` as a substitute for classification

## 3. Structured Logging Fields

The operational log contract is [OperationalLogRecord](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/observability.py).

Required structured fields for all operational logs:

- `event_name`
- `category`
- `trace_id`
- `severity`
- `recorded_at_utc`

Required when available:

- `case_id`
- `document_id`
- `review_task_id`
- `workflow_run_id`
- `workflow_step`
- `queue_name`
- `actor_id`
- `actor_type`
- `integration_name`
- `provider_request_id`
- `attempt_no`
- `reason_codes`

Optional quality fields:

- `confidence_score`
- `evidence_refs`

Log hygiene rules:

- PII or raw document text must not be emitted into general operational logs
- use evidence refs, artifact ids, and hashes instead of copying document content
- stack traces are allowed only in protected engineering sinks, not in business-facing audit payloads
- log levels must be consistent: `INFO`, `WARN`, `ERROR`, `CRITICAL`

## 4. Workflow Event Tracking

Workflow tracking must align with the explicit workflow implementation.

Track these workflow events:

- workflow start requested
- workflow run created
- workflow step scheduled
- workflow step started
- workflow step heartbeat missed
- workflow step retried
- workflow step completed
- workflow step timed out
- workflow step failed
- workflow waiting on manual review
- workflow resumed from review signal
- workflow reached terminal state

Emit a workflow event log at:

- workflow creation
- every step boundary
- every retry decision
- every manual-review pause and resume
- every abnormal termination

Required workflow tracking fields:

- `trace_id`
- `workflow_run_id`
- `case_id`
- `workflow_step`
- `attempt_no`
- `status`
- `latest_error_code` when applicable
- `queue_name`

## 5. Metrics To Emit

The MVP metric names are declared in [observability.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/observability.py).

Core metrics:

- `ops_agent_cases_created_total`
- `ops_agent_case_state_transitions_total`
- `ops_agent_case_processing_duration_seconds`
- `ops_agent_workflow_step_started_total`
- `ops_agent_workflow_step_completed_total`
- `ops_agent_workflow_step_failed_total`
- `ops_agent_workflow_step_retry_total`
- `ops_agent_workflow_step_duration_seconds`
- `ops_agent_review_tasks_open`
- `ops_agent_review_task_age_seconds`
- `ops_agent_review_actions_total`
- `ops_agent_queue_depth`
- `ops_agent_queue_oldest_age_seconds`
- `ops_agent_integration_requests_total`
- `ops_agent_integration_failures_total`
- `ops_agent_integration_latency_seconds`
- `ops_agent_agent_low_confidence_total`
- `ops_agent_agent_schema_validation_failures_total`
- `ops_agent_agent_quality_score`
- `ops_agent_audit_write_failures_total`

Metric labeling guidance:

- `workflow_type`
- `priority`
- `queue_name`
- `step_name`
- `provider`
- `result`
- `reason_code`
- `review_queue`

## 6. Error Metrics

Emit counters for:

- API 4xx by route and error code
- API 5xx by route
- workflow step failures by step and error code
- provider call failures by provider and operation
- schema validation failures by capability and schema file
- audit write failures
- state transition rejection counts
- review action rejection counts

Emit error logs at the same time as metrics so debugging can correlate count spikes to events.

Rules:

- deterministic business-rule failures should be tagged separately from infrastructure failures
- retryable vs non-retryable must be a metric dimension
- audit pipeline failures require immediate operator visibility

## 7. Latency Metrics

Latency metrics must be histograms, not just averages.

Required latency histograms:

- API request duration by route and status code
- full case processing duration from creation to closeable state
- workflow step duration by step name
- provider round-trip latency by provider operation
- review task age and claim-to-complete duration
- correction-to-revalidation latency
- audit write latency

Latency emission points:

- request completion
- workflow step completion
- provider response receipt
- review task claim/completion
- audit persistence completion

## 8. Queue Metrics

Queue metrics are required for both machine queues and human review queues.

Machine queue metrics:

- queue depth
- oldest message age
- in-flight job count
- retry backlog count
- dead-letter count if available

Human review queue metrics:

- open tasks by queue
- unclaimed task age percentile
- claimed task age percentile
- escalation volume by queue
- SLA-breaching task count

Emit queue metrics:

- on every queue poll cycle
- after enqueue/dequeue operations
- when review task status changes

## 9. Confidence And Quality Monitoring Signals

Quality monitoring is distinct from availability monitoring.

Track:

- low-confidence result count by capability
- confidence distribution by document type and field
- missing-evidence rate
- schema validation failure rate
- manual correction rate by extracted field
- revalidation failure rate after correction
- disagreement rate across repeated model attempts
- review override rate versus machine recommendation
- false-positive escalation rate when known from human outcomes

Rules:

- confidence metrics must always be tied to model/prompt/rule versions
- quality metrics should feed release decisions for prompts and models
- do not aggregate away the responsible capability, schema, and version dimensions

## 10. Dashboards To Support Ops And Engineering

Required MVP dashboards:

1. operations queue dashboard
   Shows:
   queue depth, aged tasks, claim times, open escalations, SLA breaches

2. workflow health dashboard
   Shows:
   active workflows, step failure counts, retries, timeout rates, terminal outcomes

3. provider/integration dashboard
   Shows:
   OCR latency, extraction latency, provider failures, schema-validation failures

4. audit pipeline dashboard
   Shows:
   audit write throughput, audit write latency, audit write failures

5. quality dashboard
   Shows:
   low-confidence trends, correction rates, review overrides, model/prompt version splits

6. API reliability dashboard
   Shows:
   request rate, 4xx/5xx rates, route latency, auth failures

## 11. Alerting Hooks

MVP alerts should be wired to engineering on-call and operations supervisors.

Engineering alerts:

- workflow step failure rate above threshold
- queue oldest age above threshold
- repeated provider timeout spike
- audit write failure count above zero sustained for 5 minutes
- API 5xx rate above threshold
- schema validation failure spike after release

Operations alerts:

- review queue SLA breach
- supervisor escalation queue growth
- fraud/compliance queue backlog growth
- case processing latency above agreed SLA

Alert payload should include:

- alert name
- severity
- environment
- primary metric values
- dashboard link
- sample trace ids or workflow ids
- recent deployment version

## 12. MVP Observability Baseline

MVP implementation should include:

- JSON structured operational logs
- append-only audit event writes
- metric counters/gauges/histograms for the core flows
- trace id propagation across API, workflow, provider calls, and reviewer actions
- baseline dashboards for ops, workflow health, provider health, and audit health
- alerting for workflow failures, queue age, API 5xx, and audit pipeline failures

MVP non-goals:

- full distributed tracing across every dependency
- log analytics on raw document content
- predictive anomaly detection
- hash-chained audit verification

## Emission Matrix

| Event | Audit log | Operational log | Metric |
|---|---|---|---|
| case created | yes | yes | `cases_created_total` |
| document registered | yes | yes | none |
| workflow step started | yes | yes | `workflow_step_started_total` |
| workflow step completed | yes | yes | `workflow_step_completed_total`, duration histogram |
| workflow step failed | yes | yes | `workflow_step_failed_total` |
| workflow step retried | yes | yes | `workflow_step_retry_total` |
| low-confidence agent output | yes | yes | `agent_low_confidence_total` |
| schema validation failure | no | yes | `agent_schema_validation_failures_total` |
| manual correction submitted | yes | yes | `review_actions_total` |
| review queue aged beyond SLA | no | yes | queue age gauges/histograms |
| audit write failure | no self-write | yes | `audit_write_failures_total` |

## Acceptance Criteria

- audit and operational logs are distinct in storage, retention, and intended use
- every workflow step boundary emits both observable logs and metrics
- evidence-linked machine or reviewer actions can be traced from audit event to workflow run
- dashboards support both operational triage and engineering debugging
- alerting is tied to concrete failure and backlog conditions, not generic log scraping

# Workflow Orchestration Implementation Specification

This specification defines the explicit orchestration behavior for the banking Document Processing Agent (Ops Agent). It is aligned to the current scaffold in [state_machine.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/state_machine.py), [case_workflow.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/workflows/case_workflow.py), [policy.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/workflows/policy.py), and [workflow_contracts.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/workflow_contracts.py).

## Assumptions

- The workflow engine target is Temporal.
- PostgreSQL remains the durable source of truth for workflow state and review state.
- Object storage contains documents and large derived artifacts.
- No workflow step is allowed to silently approve, reject, or close a case.
- All material workflow events must create durable audit records.

## 1. Workflow Stages

The canonical MVP workflow stages are:

1. intake registration
2. document storage confirmation
3. queue dispatch
4. OCR
5. layout analysis
6. document classification
7. field extraction
8. validation and compliance evaluation
9. routing decision
10. manual review gate
11. reviewer correction or escalation
12. revalidation
13. outcome recording and closure

Stage ownership for implementation:

| Stage | Primary owner | Output |
|---|---|---|
| intake registration | API + workflow starter | case row, document rows, workflow start command |
| OCR | OCR activity worker | OCR artifact, OCR run/result rows |
| layout analysis | parser/layout worker | parsing artifact, page structure |
| document classification | classifier worker | classification result |
| field extraction | extractor worker | extraction result, evidence refs |
| validation and compliance evaluation | rules worker | validation findings, risk/compliance findings |
| routing decision | policy/decision worker | recommended route, reason codes |
| manual review gate | workflow + review service | review task or direct next state |
| reviewer correction or escalation | reviewer UI + review service | manual review action, corrected fields |
| revalidation | rules worker | updated validation set |
| outcome recording and closure | review service + workflow | approved, rejected, escalated, or closed case |

## 2. State Machine Transitions

The orchestration layer must use the explicit case state machine in [state_machine.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/state_machine.py). Allowed transitions are:

- `received -> stored`
- `stored -> queued`
- `queued -> processing`
- `queued -> review_required`
- `processing -> validated`
- `processing -> failed`
- `processing -> review_required`
- `validated -> review_required`
- `validated -> approved`
- `validated -> rejected`
- `review_required -> in_review`
- `review_required -> escalated`
- `in_review -> corrected`
- `in_review -> escalated`
- `in_review -> approved`
- `in_review -> rejected`
- `corrected -> validated`
- `corrected -> review_required`
- `escalated -> in_review`
- `escalated -> closed`
- `approved -> closed`
- `rejected -> closed`
- `failed -> review_required`
- `failed -> closed`

Rules:

- Every transition must be driven by a named command.
- Transition intent must be persisted before external side effects are considered complete.
- No background worker may mutate case status directly without passing through the state machine guard.
- Manual review does not bypass `validated`, `approved`, or `rejected`; it only changes how the case reaches them.

## 3. Async Job Boundaries

Each async boundary must be a durable workflow activity or workflow signal boundary.

MVP boundaries:

- API request ends after case creation and workflow start request persistence.
- Workflow starter consumes the durable start command and creates a workflow run.
- OCR is its own activity boundary.
- Layout analysis is its own activity boundary.
- Classification is its own activity boundary.
- Extraction is its own activity boundary.
- Validation and compliance evaluation are their own activity boundary.
- Decision routing is its own activity boundary.
- Review wait state is a workflow pause boundary.
- Reviewer completion is a workflow signal boundary.
- Revalidation after correction is a new validation activity boundary.

Do not combine OCR, extraction, and validation into one opaque worker job. Those steps need independent retry, timeout, evidence, and audit behavior.

## 4. Queue And Job Responsibilities

Queue names and step policies are defined in [policy.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/workflows/policy.py).

MVP queue responsibilities:

| Queue | Responsibility |
|---|---|
| `ops_agent_ingestion` | persist workflow registration side effects, confirm document storage metadata |
| `ops_agent_ocr` | invoke OCR provider, persist OCR artifacts, return page-level confidence |
| `ops_agent_layout` | parse layout and page structure, persist layout artifact |
| `ops_agent_classification` | classify document type, return confidence and candidate labels |
| `ops_agent_extraction` | extract normalized fields with evidence refs |
| `ops_agent_validation` | run business validation and compliance controls |
| `ops_agent_decision` | compute safe recommended route and reason codes |
| `ops_agent_review_gate` | create review task or advance to terminal human-approved state |

Review queues for human work:

- `ops_review_general`
- `ops_review_compliance`
- `ops_review_fraud`
- `ops_review_supervisor`

Queue assignment rules:

- fraud or sanctions reason codes route to `ops_review_fraud`
- AML, KYC, or policy breach reason codes route to `ops_review_compliance`
- repeated failures, lock conditions, or unresolved escalations route to `ops_review_supervisor`
- all other low-confidence or ambiguity cases route to `ops_review_general`

## 5. Retry Rules

Retry policy defaults are codified in [policy.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/workflows/policy.py).

MVP retry rules:

- ingestion: no retry by default
- OCR: up to 3 attempts, exponential backoff from 30s to 300s
- layout: up to 3 attempts, exponential backoff from 30s to 300s
- classification: up to 2 attempts, exponential backoff from 30s to 180s
- extraction: up to 2 attempts, exponential backoff from 30s to 180s
- validation: up to 2 attempts, exponential backoff from 15s to 120s
- decision: up to 2 attempts, exponential backoff from 15s to 120s
- review gate: no retry by default

Non-retryable error examples:

- unsupported document type
- corrupt document payload
- schema mismatch in required upstream payload
- invalid state transition
- invalid reviewer command for current case state

Rules:

- retry only transient infrastructure or provider failures
- do not retry deterministic policy or validation failures
- every retry attempt must create a step-run update and audit event
- after retry exhaustion, route to `failed` or `review_required` explicitly

## 6. Timeout Rules

Timeout defaults are also codified in [policy.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/workflows/policy.py).

MVP timeouts:

| Step | Start-to-close | Schedule-to-close | Heartbeat |
|---|---|---|---|
| ingestion | 30s | 120s | none |
| OCR | 300s | 1200s | 60s |
| layout | 180s | 900s | 60s |
| classification | 120s | 600s | none |
| extraction | 180s | 900s | 60s |
| validation | 120s | 600s | none |
| decision | 60s | 300s | none |
| review gate | 30s | 120s | none |

Human review timeout behavior:

- review tasks are not auto-completed by timeout
- SLA breach creates an alert event and supervisor queue item
- the case remains in `review_required` or `in_review` until a human acts

## 7. Low-Confidence Routing

Low confidence is a routing condition, not an autonomous rejection condition.

MVP thresholds:

- OCR page confidence below `0.85` triggers review consideration
- classification top-label confidence below `0.80` triggers review
- extraction confidence below `0.85` for required fields triggers review
- review gate applies a final conservative threshold of `0.90` when summarizing overall machine confidence

Additional low-confidence rules:

- conflicting candidate values for the same required field force review
- missing required evidence refs force review
- missing required fields force review
- model disagreement across repeated attempts forces review

Low-confidence routing outputs:

- `recommended_route = review_required`
- explicit `reason_codes`
- linked evidence refs
- queue assignment
- audit event

## 8. Manual Review Routing

Manual review is mandatory for:

- low-confidence required fields
- any critical validation failure
- any possible sanctions, AML, or fraud indicator
- document type ambiguity
- extraction conflicts across pages or documents
- workflow retry exhaustion where business interpretation is still possible
- any reviewer-initiated escalation

Review routing behavior:

1. workflow sets case to `review_required`
2. review task is created with queue, reason codes, and evidence bundle
3. reviewer claims task, moving case to `in_review`
4. reviewer can correct, escalate, approve, or reject within allowed state transitions
5. corrections move case to `corrected`
6. corrected cases must pass revalidation before closure

Review actions must always capture:

- actor id
- action type
- reason code
- optional comment
- evidence refs
- timestamp
- resulting state transition

## 9. Audit Event Creation Points

Audit events are required at these points:

- case created
- document metadata registered
- document artifact stored
- workflow start command persisted
- workflow run started
- each step started
- each step completed
- each step retried
- each step timed out
- each step failed
- case status transitioned
- review task created
- review task claimed
- correction submitted
- revalidation requested
- escalation submitted
- decision recorded
- case approved, rejected, failed, or closed
- supervisor alert created

Minimum audit payload:

- `event_id`
- `trace_id`
- `case_id`
- `workflow_run_id` where applicable
- `resource_type`
- `resource_id`
- `action`
- `actor_type`
- `actor_id`
- `details`
- `occurred_at_utc`

## 10. Failure Recovery Behavior

Failure recovery must be explicit and observable.

Transient dependency failure:

- keep case in `processing`
- retry according to policy
- persist latest error code and retry count
- emit audit event and structured log

Retry exhausted with unresolved business ambiguity:

- move case to `review_required`
- create review task in supervisor or specialized queue
- preserve failed step context and input/output artifact refs

Retry exhausted with unrecoverable technical failure:

- move case to `failed`
- require manual recovery command or explicit closure
- do not silently drop the workflow

Worker crash or workflow restart:

- reload durable workflow status
- resume from the last completed step boundary
- never rerun a completed side-effecting activity without idempotency check

Review path recovery:

- if a reviewer session drops, task remains claimed until claim timeout or supervisor intervention policy runs
- no correction is committed unless the review action is durably stored

## 11. Idempotency Expectations

Idempotency is mandatory for all workflow commands and step side effects.

Required idempotency keys:

- workflow start: `case_id + workflow_definition_version + document_version_set_hash`
- step activity execution: `workflow_run_id + step_name + document_id`
- review task creation: `case_id + workflow_run_id + review_reason_set_hash`
- review signal handling: `review_task_id + action_id`
- audit event write: unique `event_id`, plus natural-key dedupe where practical

Rules:

- duplicate workflow start commands must return the existing active workflow run
- duplicate activity completion callbacks must be ignored after first durable commit
- object storage artifact writes must use deterministic keys or recorded content hashes
- manual correction submission must not create duplicate corrections if the same `action_id` is replayed

## 12. MVP Orchestration Implementation

Recommended MVP implementation:

1. API persists case, documents, and workflow start command in one transaction.
2. Outbox processor publishes `WorkflowStartCommand`.
3. Temporal workflow starts and records `workflow_run`.
4. Workflow transitions:
   `received -> stored -> queued -> processing`
5. Activities execute in order:
   `ingestion -> ocr -> layout -> classification -> extraction -> validation -> decision -> review_gate`
6. Each activity persists:
   step run row,
   machine result rows,
   artifact refs,
   audit events
7. If review is required, workflow creates review task and waits for `ReviewCompletionSignal`.
8. Reviewer actions route to:
   `in_review -> corrected -> validated`
   or `in_review -> approved`
   or `in_review -> rejected`
   or `in_review -> escalated`
9. Closure only happens after an explicit terminal command.

Concrete MVP implementation assets already present:

- [workflow_contracts.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/workflow_contracts.py)
- [case_workflow.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/workflows/case_workflow.py)
- [policy.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/workflows/policy.py)
- [state_machine.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/state_machine.py)

MVP non-goals:

- no autonomous case approval without explicit policy-backed terminal command
- no event-stream fan-out beyond outbox to workflow starter
- no dynamic model routing across many providers

## 13. Later-Scale Orchestration Improvements

After MVP stabilization, add:

- dedicated workflow per document class where processing materially differs
- dead-letter replay tooling with operator approvals
- adaptive retry by provider health and error class
- queue depth autoscaling and priority-aware dispatch
- supervisor rebalancing for aged review queues
- event streaming for read models and search projections
- workflow snapshots and replay diagnostics for audit or regulator requests
- policy pack version rollout controls and canary execution
- immutable audit hash chaining and signed export manifests
- workflow dashboards for retry hot spots, queue age, and human-review bottlenecks

## Implementation Checks

- Hidden state transitions are prohibited.
- Every workflow pause or resume point must be durable.
- Every routing decision must be explainable with reason codes and evidence refs.
- Manual review remains the control point for ambiguity, risk, or policy-sensitive outcomes.
- Observability data must allow one case to be traced across API, workflow, workers, and reviewer actions.

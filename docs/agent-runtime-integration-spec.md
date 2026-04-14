# Agent Runtime Integration Specification

This specification defines how prompt-driven document-processing agents integrate into the banking Ops Agent runtime. It is designed for conservative, schema-bound, auditable execution and is aligned to [prompt_registry.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/prompt_registry.py), [runtime_models.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/agents/runtime_models.py), [runtime.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/agents/runtime.py), and the shared schemas in [contracts/jsonschema](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/contracts/jsonschema).

## 1. Prompt Storage And Versioning

Prompt definitions are stored in the application repository and loaded through the prompt registry.

Current implementation anchor:

- [prompt_registry.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/prompt_registry.py)

Each prompt definition must include:

- `prompt_id`
- `prompt_version`
- `owner`
- `role_boundary`
- `allowed_statuses`
- `escalation_targets`
- `schema_name`
- `schema_file`
- `requires_evidence`
- `reasoning_summary_max_chars`
- `change_control_required`

Versioning rules:

- prompt content changes require a new `prompt_version`
- semantic prompt behavior changes require a new `prompt_id`
- each prompt version must be linked to a concrete output schema file
- released workflow runs must store the prompt version they actually executed
- rollback means selecting a previous prompt id/version pair in config, not editing history in place

Recommended storage model:

- repo-managed source of truth for prompt metadata and templates
- database table or artifact record for execution history and release pinning
- object storage for raw rendered prompts and raw model outputs when retention policy allows

## 2. How Each Agent Is Invoked

Each agent capability is invoked through a bounded runtime request, not by arbitrary free-form prompting.

Current implementation anchor:

- [runtime_models.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/agents/runtime_models.py)
- [runtime.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/agents/runtime.py)

Invocation flow:

1. workflow step chooses a capability
2. runtime loads prompt definition from registry
3. runtime builds `AgentInvocationRequest`
4. request includes:
   trace context,
   workflow context,
   schema binding,
   idempotency key,
   evidence bundle,
   allowed statuses,
   allowed escalation targets
5. runtime sends the request to a structured-output adapter
6. raw output is validated before any case mutation occurs
7. validated result is converted into workflow-side routing or persisted results

MVP supported capabilities:

- `ocr_reconcile`
- `document_classify_tiebreak`
- `field_extract_reconcile`
- `compliance_review_summary`
- `review_copilot`

Hard runtime rule:

- the agent never receives authority to approve, reject, close, or clear a case

## 3. How Agent Outputs Are Validated

Validation happens in two layers:

1. registry-policy validation
2. schema validation

Registry-policy validation checks:

- capability exists
- prompt id matches the capability
- prompt version matches the active registry entry
- schema file and schema name match the declared capability

Schema validation checks:

- output is valid JSON object
- output matches the declared JSON schema
- required fields are present
- enumerated `status` and `escalation_target` remain within policy
- confidence fields are numeric and bounded
- evidence refs match the expected object structure

Only validated outputs may be persisted as machine results or used for workflow routing.

## 4. How Agent Handoffs Are Handled

Agent handoffs must be explicit and typed.

Current implementation anchor:

- `AgentHandoff` in [runtime_models.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/agents/runtime_models.py)

Handoff payload must include:

- `from_agent`
- `to_agent`
- `handoff_reason`
- `input_artifact_ids`
- `inherited_reason_codes`
- `evidence_refs`

Rules:

- handoffs can only occur across approved workflow step boundaries
- downstream agents must receive the prior output as input data, not implicit shared state
- the downstream agent must declare its own schema and role boundary
- handoffs must be logged and auditable

Example:

- OCR reconcile agent returns `needs_review` with ambiguous spans
- extraction reconcile agent may be invoked with the OCR artifact and explicit handoff metadata
- if ambiguity remains, workflow routes to review instead of chaining further autonomous agents

## 5. How Schema Enforcement Works

Schema enforcement is mandatory and must happen before result persistence.

Implementation approach for MVP:

- JSON schemas live under [contracts/jsonschema](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/contracts/jsonschema)
- each prompt definition names one schema file
- runtime validator loads the schema file and validates the output payload
- runtime blocks any result that:
  fails schema validation,
  contains unknown control fields,
  violates allowed status or escalation policy

Schema enforcement principles:

- schema-bound structured outputs only
- no plain-text-only result paths
- no hidden control flags outside the schema
- no silent coercion of malformed model output into accepted business objects

## 6. How Low-Confidence Outputs Are Escalated

Low-confidence outputs are routing signals, not autonomous decisions.

Escalation logic:

- if agent returns `needs_review`, case goes to review path
- if agent returns `insufficient_evidence`, case goes to review or resubmission path
- if confidence is below workflow threshold for a required field, route to review even if status is `completed`
- if reason codes indicate risk or policy sensitivity, route to specialist review queues

Escalation targets must be limited to the prompt definition’s allowed list.

Examples:

- OCR ambiguity: `ops_review`
- classification ambiguity: `ops_review`
- compliance summary with sanctions/fraud signals: `compliance_review` or `fraud_review`
- unrecoverable evidence gap: `manual_resubmission`

## 7. How Prompt Changes Are Governed

Prompt changes are controlled like code changes.

Required governance for MVP:

- prompt files and registry changes go through pull request review
- each prompt change references an issue, ticket, or change request
- owner approval is required for prompts marked `change_control_required`
- prompt changes must include:
  intended behavior change,
  affected schema,
  rollback version,
  evaluation notes or sample test cases

Release rules:

- production workflow pins prompt version by deployment config
- do not mutate a released prompt in place
- rollback is done by configuration switch to the previous approved version

## 8. How Agent Output Failures Are Handled

Failure classes:

- provider invocation failure
- timeout
- malformed JSON
- schema validation failure
- policy validation failure
- missing evidence or missing required context

Failure handling behavior:

- transient provider failure: retry per workflow policy
- malformed or schema-invalid output: mark non-retryable unless provider-specific auto-repair is explicitly implemented
- policy-invalid output: non-retryable and treated as runtime safety failure
- repeated failure exhaustion: route to manual review or fail the step explicitly

Current implementation anchor:

- `AgentFailure` and `AgentRuntimeError` in [runtime_models.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/agents/runtime_models.py) and [runtime.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/agents/runtime.py)

Rules:

- never silently drop invalid agent output
- never pass raw invalid output downstream
- preserve provider request id and artifact reference where possible
- always emit audit/log records for failure

## 9. How Audit Records Capture Agent Reasoning Summaries Safely

Audit must capture reviewer-safe summaries, not unrestricted reasoning traces.

Current implementation anchor:

- [audit_logging.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/src/ops_agent/audit_logging.py)

Allowed audit fields for agent execution:

- capability
- prompt id
- prompt version
- schema name and file
- model name and version
- status
- escalation target
- confidence score
- reason codes
- evidence refs
- raw output artifact id
- bounded `reasoning_summary`

Safety rules:

- do not store raw chain-of-thought in audit logs
- store only concise, reviewer-safe reasoning summaries
- reasoning summaries must be normalized and length-limited
- sensitive document text should be referenced through evidence refs or artifact ids, not copied into audit payloads unless explicitly required

## 10. MVP Runtime Integration Design

Recommended MVP runtime design:

1. Workflow step builds `AgentInvocationContext`.
2. Workflow step selects capability from registry.
3. Runtime builds `AgentInvocationRequest` with:
   prompt metadata,
   role boundary,
   evidence bundle,
   input payload,
   allowed statuses,
   allowed escalation targets,
   idempotency key
4. Structured agent adapter invokes the chosen model with `temperature=0.0`.
5. Runtime validates output against schema and policy.
6. Runtime returns `AgentValidatedResult`.
7. Workflow writes:
   machine result rows,
   artifact reference,
   safe audit record,
   workflow routing outcome
8. If output is low-confidence or policy-sensitive, workflow routes to human review.

MVP non-goals:

- no autonomous multi-agent planning loop
- no self-modifying prompts
- no dynamic tool access granted to the agent
- no agent-to-agent conversation outside declared handoff payloads
- no free-form reviewer-facing output without schema validation

## Backend Implementation Notes

Recommended service boundary:

- `AgentRuntimeService` owns registry checks, schema binding, policy checks, and safe audit shaping
- workflow activities own provider selection and retry behavior
- persistence layer stores raw artifacts and validated result metadata separately

Recommended persistence outputs per invocation:

- invocation request envelope
- prompt id/version and model id/version
- schema file/version
- raw output artifact pointer
- validated result payload
- audit summary payload
- failure payload when applicable

## Acceptance Criteria

- every prompt-driven step is schema-bound
- every invocation is versioned and replayable
- every output is policy-checked before affecting workflow state
- low-confidence or risky outputs always route to human review
- prompt rollback can be performed by configuration without data loss

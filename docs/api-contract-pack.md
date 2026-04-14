# Ops Agent API Contract Pack

Primary artifact: [ops-agent-contract-pack.yaml](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/openapi/ops-agent-contract-pack.yaml)

## Endpoint Grouping

- `System`: health and runtime checks
- `Cases`: create, list, retrieve, status, and results
- `Documents`: document registration and metadata lookup
- `Processing`: explicit async processing trigger
- `Decisions`: decision history and manual decision submission
- `Review`: review queue, claim, correction, escalation, revalidation, close
- `Audit`: immutable audit events and manual review actions
- `Internal`: workflow start, status, and review-complete signal

## Reuse Rules

- Shared objects live in `components/schemas`.
- Reusable responses live in `components/responses`.
- `ErrorObject` is the single standard error shape.
- Mutating endpoints expose state-safe metadata in `x-ops-agent-state-guards`.

## State-Safe Validation Pattern

Mutation handlers should validate in this order:

1. authenticate caller
2. authorize role
3. validate request body shape
4. load current case or task state
5. compare against allowed source states
6. enforce idempotency when `Idempotency-Key` is present
7. persist business mutation and audit event in the same operation boundary

Conflict responses should return:

- `error_code: state_transition_conflict`
- `details.requested_operation`
- `details.current_state`
- `details.allowed_states`

Validation failures should return:

- `error_code: request_validation_failed`
- `details.field_errors[]`

## Future Code Generation Notes

- Generate SDKs from `ops-agent-contract-pack.yaml`, not from the smaller MVP spec.
- Preserve string enums in TypeScript and Python models.
- Do not flatten `ErrorObject.details` into an untyped map everywhere; keep conflict and validation detail helpers.
- Once the runtime moves to response envelopes, publish a new versioned contract instead of mutating this one in place.

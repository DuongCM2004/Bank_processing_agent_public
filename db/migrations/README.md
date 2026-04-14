# Ops Agent Migration Pack

This folder is the MVP database migration pack for the banking Document Processing Agent.

## Migration Order

1. `0001_init_schemas.sql`
   Creates logical schemas: `ops_core`, `ops_ai`, `ops_rules`, `ops_review`, `ops_audit`
2. `0002_core_tables.sql`
   Creates case, document, workflow, and outbox tables
3. `0003_ai_rules_review_audit_tables.sql`
   Creates extraction, validation, decision, review, and audit tables
4. `0004_document_pages_identity.sql`
   Adds document-page support and identity tables
5. `0005_ai_evidence_compliance.sql`
   Adds OCR, classification, evidence-linking, compliance, and risk tables
6. `0006_status_constraints_and_indexes.sql`
   Adds workflow-safe status constraints and operational indexes

## MVP Table Groups

- `ops_core.*`
  System-of-record case state, document metadata, workflow execution state, and async outbox
- `ops_ai.*`
  OCR, classification, extraction, artifacts, and extracted-field evidence
- `ops_rules.*`
  Validation, compliance, risk findings, and decision inputs
- `ops_review.*`
  Review queue and manual review actions
- `ops_audit.*`
  Append-only audit history
- `ops_identity.*`
  Local user and role mappings for internal operations

## Relationship Model

- `case -> document -> document_version -> document_page`
- `case -> workflow_run -> workflow_step_run`
- `document_version -> artifact`
- `artifact/run -> extracted_field or validation_result -> evidence_ref`
- `case -> review_task -> review_action`
- `case -> audit_event`

## Status Typing Approach

The MVP pack uses `TEXT` columns with explicit `CHECK` constraints for core workflow states instead of PostgreSQL enum types.

Reason:

- safer backward-compatible rollout when status vocabularies expand
- easier multi-service deployment sequencing
- no enum-alter coordination requirement during urgent operational releases

Use PostgreSQL enums later only if the status set becomes genuinely stable across services.

## Audit And Traceability Expectations

- Every case state transition should write both:
  - a durable current state update
  - an append-only history or audit record
- `trace_id` should be preserved on workflow, review, outbox, and audit tables
- Evidence tables must always retain case/document linkage

## Backward-Compatible Migration Evolution

When evolving this pack:

1. add new nullable columns before making them required
2. backfill in a separate migration where needed
3. add constraints only after existing data is compatible
4. prefer additive tables over destructive table rewrites
5. avoid renaming status values in place without compatibility windows
6. never mutate or delete audit history in schema migrations
7. add indexes after confirming query shape and write cost

## Operational Notes

- Apply migrations in order with a versioned migration runner.
- Do not skip directly to later migrations on new environments.
- Keep DDL and seed/reference data separate.
- Treat this pack as the baseline for Postgres repository implementation.

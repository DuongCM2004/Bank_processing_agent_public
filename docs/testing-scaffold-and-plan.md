# Testing Scaffold And Engineering Test Plan

This testing plan is build-oriented and aligned to the current repository. It expands the existing `pytest` suite into a structure that supports banking-safe backend behavior, workflow correctness, messy document handling, and controlled AI/runtime testing.

## 1. Test Folder Structure

Recommended target structure:

```text
tests/
  conftest.py
  testkit.py
  unit/
    domain/
    application/
    workflows/
    security/
    observability/
  integration/
    api/
    persistence/
    workflow_runtime/
    providers/
  e2e/
    workflow/
    review/
  fixtures/
    cases/
    documents/
    provider_outputs/
  stubs/
    providers.py
  examples/
    unit_case_state_machine_example.py
    integration_review_flow_example.py
    e2e_workflow_failure_example.py
```

Current repo-compatible near-term structure:

- keep existing top-level `tests/test_*.py` files
- add reusable helpers in `tests/testkit.py`
- add deterministic stubs in `tests/stubs/providers.py`
- add scenario fixtures in `tests/fixtures/`
- start new suites under `tests/unit`, `tests/integration`, and `tests/e2e`

## 2. Unit Test Scope

Unit tests must cover logic that can fail safely without external services.

Required unit scope:

- case state machine transitions and invalid transition rejection
- workflow step policy defaults and retry/timeout policy mapping
- prompt registry and runtime policy validation
- schema selection and safe reasoning-summary truncation
- authorization matrix and protected action mapping
- observability event builders and metric naming integrity
- service-layer guards for:
  closed-case document rejection,
  invalid review actions,
  duplicate command idempotency,
  low-confidence routing

Unit tests must not depend on:

- live databases
- object storage
- real OCR or LLM providers
- real Temporal runtime

## 3. Integration Test Scope

Integration tests must verify component boundaries and persistence behavior.

Required integration scope:

- FastAPI route to application service behavior
- Postgres migration application from clean database
- repository persistence for:
  cases,
  documents,
  workflow runs,
  review tasks,
  audit events
- object storage adapter behavior with stubbed private bucket client
- internal workflow command and signal contract validation
- auth middleware and role enforcement on public vs internal routes
- provider adapter integration with deterministic stubs

Integration tests should run in CI with local service containers when those integrations are added.

## 4. End-To-End Workflow Test Scope

End-to-end tests should prove the banking-safe path through the full workflow.

Required MVP e2e scenarios:

1. happy-path reviewer-assisted case
   case created -> review task claimed -> field corrected -> revalidated -> closed

2. low-confidence machine result
   OCR or extraction confidence below threshold -> review task created -> no auto-close

3. workflow retry exhaustion
   provider timeout repeated -> case routed to `review_required` or `failed` explicitly

4. escalation path
   reviewer escalates -> case enters `escalated` -> supervisor claims -> terminal action recorded

5. decision safety path
   machine route recommended but reviewer remains final decision-maker

E2E tests must assert:

- visible durable state at every step
- audit events created at every mutation
- no hidden state transitions
- evidence refs preserved from machine output to reviewer action

## 5. Test Data Strategy

Use layered test data:

- hand-authored deterministic fixtures for critical control paths
- synthetic “messy” fixtures for OCR/layout ambiguity
- versioned JSON fixtures for provider outputs
- minimal golden cases for regression

Data strategy rules:

- never use real customer documents
- fixtures must be anonymized and synthetic
- every fixture should carry a scenario id and short description
- keep one small canonical fixture per major document class first

Recommended fixture classes:

- clean single-document KYC submission
- blurry phone capture of ID
- multi-page income statement with rotated page
- mixed-resolution PDF bundle
- duplicate upload of same document version
- conflicting values across pages
- missing signature or cropped footer
- sanctions/AML reason-code fixture

## 6. Mock/Stub Strategy For OCR And AI Services

Do not use live OCR or live LLM services in standard CI.

Default strategy:

- unit tests use in-process deterministic stubs
- integration tests use stub adapters returning versioned JSON payloads
- nightly or gated non-blocking suites may run against sandbox providers later

Required stub behavior:

- deterministic outputs by scenario id
- configurable latency simulation
- configurable retryable vs non-retryable failure simulation
- explicit confidence scores
- evidence refs included in success payloads

Provider stub types:

- OCR stub
- classifier stub
- extractor stub
- validation stub
- decision stub

## 7. Edge-Case Document Scenarios

Banking-safe coverage must include messy real-world documents.

Priority edge cases:

- low-resolution ID scan
- partially cropped passport image
- rotated or upside-down page
- duplicate pages in one PDF
- blank separator page inside a bundle
- mixed-language labels
- handwritten correction near typed value
- conflicting account number on two pages
- illegible signature area
- dark background photo causing OCR span fragmentation
- missing required field with strong but incomplete evidence
- same document uploaded twice with different filenames
- oversized file upload
- unsupported MIME type renamed as PDF
- possible tampering or fraud marker reason code

Each scenario must test:

- workflow routing
- confidence handling
- evidence preservation
- review requirement where ambiguity remains

## 8. Regression Test Priorities

Highest regression priority:

1. state transition safety
2. authz and internal-route isolation
3. audit event creation and append-only behavior
4. low-confidence and risk routing
5. review correction and revalidation loop
6. schema-bound agent output validation
7. upload validation and private storage access

Any change in these areas must trigger:

- focused unit tests
- relevant integration tests
- at least one workflow path regression test

## 9. Release Quality Gates For MVP

Minimum blocking gates for MVP release:

- all unit tests pass
- all integration tests pass
- e2e happy path and low-confidence routing path pass
- authz negative tests pass for privileged routes
- migration apply test passes on clean database
- JSON/OpenAPI/schema asset validation passes
- no unresolved critical or high severity defects in:
  auth,
  audit,
  workflow state,
  upload security

Recommended additional gate:

- release-candidate smoke run against staging with stub providers and real auth

## 10. Example Test Case Skeletons

The repository now includes reusable examples and test helpers:

- [testkit.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/tests/testkit.py)
- [providers.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/tests/stubs/providers.py)
- [kyc_clean_case.json](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/tests/fixtures/cases/kyc_clean_case.json)
- [ocr_low_confidence_case.json](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/tests/fixtures/cases/ocr_low_confidence_case.json)
- [workflow_retry_exhausted_case.json](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/tests/fixtures/cases/workflow_retry_exhausted_case.json)
- [unit_case_state_machine_example.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/tests/examples/unit_case_state_machine_example.py)
- [integration_review_flow_example.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/tests/examples/integration_review_flow_example.py)
- [e2e_workflow_failure_example.py](/D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/tests/examples/e2e_workflow_failure_example.py)

Example test case shapes:

1. unit: invalid direct transition
   assert `review_required -> closed` is rejected

2. integration: review correction loop
   create case -> claim task -> submit correction -> revalidate -> assert audit history

3. e2e: OCR retry exhaustion
   inject retryable provider failure twice -> assert third attempt routes case to review or failed state explicitly

## Engineering Execution Notes

Near-term developer tasks:

- move new logic tests under `tests/unit/`
- add Postgres integration suite once repository implementation exists
- add auth middleware negative tests as soon as bearer validation is wired
- add workflow engine integration tests once Temporal worker exists

## Acceptance Criteria

- tests are organized by behavior boundary, not just by file touched
- banking-risk scenarios force review rather than silent success
- workflow failure cases are first-class test paths
- provider stubs and fixtures are reusable across unit and integration suites

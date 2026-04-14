# QA Engineering Test Strategy for Ops Agent

## Role

QA Engineer for a banking-grade Document Processing Agent.

## Objective

Design and execute the quality strategy needed to verify correctness, robustness, reliability, safety, and regression control for the entire platform.

## Assumptions

1. The system processes sensitive identity, financial, and compliance-relevant documents for banking operations.
2. The platform contains multiple layers that must be validated together: upload, OCR, classification, extraction, validation, compliance, decisioning, human review, audit, and reporting.
3. Document quality is highly variable and many operational failures come from messy inputs rather than clean benchmark examples.
4. Any silent failure, missing evidence link, hidden retry loop, or incorrect auto-decision is considered a severe defect.
5. MVP quality strategy must be practical for the current repo while remaining extensible to the target multi-service architecture.

## Deliverables

- Testing objectives
- Test levels
- Coverage map
- Functional test areas
- Integration test areas
- End-to-end workflow tests
- Edge-case scenarios
- Low-quality document scenarios
- Human review workflow tests
- Security-sensitive behavior tests
- Regression strategy
- MVP release gate
- Scale-stage test evolution
- UAT checklist

## Dependencies

1. [ops-agent-prd.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ops-agent-prd.md)
2. [banking-document-rules.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\banking-document-rules.md)
3. [compliance-risk-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\compliance-risk-controls.md)
4. [ai-architecture.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ai-architecture.md)
5. [solution-architecture-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\solution-architecture-blueprint.md)
6. [ml-engineering-plan.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ml-engineering-plan.md)
7. [data-engineering-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\data-engineering-blueprint.md)
8. [backend-engineering-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\backend-engineering-blueprint.md)
9. [frontend-ops-dashboard-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\frontend-ops-dashboard-blueprint.md)
10. [security-architecture-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\security-architecture-controls.md)
11. [prompt-system.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\prompt-system.md)

## Risks

1. Over-focusing on model accuracy while under-testing workflow safety and evidence traceability.
2. Happy-path bias that misses low-quality scans, partial uploads, and contradictory documents.
3. Weak regression discipline causing threshold or prompt changes to silently alter operational outcomes.
4. Insufficient environment parity between local, staging, and production-like systems.
5. Test data leakage or use of non-sanitized banking documents during development and validation.

## MVP vs Scale Notes

### MVP

1. Prioritize API, workflow, validation, review routing, evidence linkage, and audit correctness.
2. Use deterministic fixture packs and a labeled messy-document set for the in-scope MVP document types.
3. Require manual sign-off for all test results affecting auto-processing thresholds.
4. Use synthetic and sanitized data only.

### Scale

1. Add production-shadow validation, broader issuer coverage, load testing, chaos testing, and model drift suites.
2. Expand E2E tests across asynchronous orchestration, Kafka/Temporal failure recovery, and regional disaster scenarios.
3. Introduce scheduled benchmark reruns for OCR, extraction, and decision consistency after every model, rule, or prompt revision.

## 1. Testing Objectives

### Quality Objectives

1. Verify that each case reaches the correct workflow state for the given evidence and business rules.
2. Verify that all extracted values remain traceable to source evidence.
3. Verify that low-confidence, conflicting, incomplete, or suspicious cases are routed to review rather than silently auto-processed.
4. Verify that audit records, review actions, and decisions are reproducible.
5. Verify that the platform remains reliable under malformed input, integration failure, and asynchronous retries.

### Test Layers

1. Unit tests
   Validate isolated business rules, schema validators, state transition rules, confidence calculations, and routing logic.
2. Contract tests
   Verify API request and response shapes, strict JSON agent payloads, event schemas, and service interface compatibility.
3. Component tests
   Validate OCR service behavior, extraction logic, validation engine, compliance engine, and decision logic against fixed fixtures.
4. Integration tests
   Verify interaction between API, persistence, queueing, workflow state changes, storage, and audit emission.
5. End-to-end tests
   Validate complete banking journeys from upload through final case status, including manual review and escalation paths.
6. Regression tests
   Detect output changes introduced by rule updates, threshold changes, prompt revisions, model replacements, and UI workflow edits.
7. Non-functional tests
   Cover latency, resilience, observability, security control enforcement, and access control behavior.

### Test Principles

1. Every critical workflow must have both happy-path and unhappy-path coverage.
2. Every auto-process path must have stronger tests than manual-review paths.
3. Expected outcomes must specify:
   final case state, review requirement, reason codes, audit events, and evidence linkage.
4. Banking defects are prioritized by operational harm:
   wrong approval or wrong rejection is more severe than delayed processing.
5. A failed compliance gate or missing audit artifact blocks release.

## 2. Test Levels

1. Unit tests
   Validate isolated business rules, schema validators, state transition rules, confidence calculations, and routing logic.
2. Contract tests
   Verify API request and response shapes, strict JSON agent payloads, event schemas, and service interface compatibility.
3. Component tests
   Validate OCR service behavior, extraction logic, validation engine, compliance engine, and decision logic against fixed fixtures.
4. Integration tests
   Verify interaction between API, persistence, queueing, workflow state changes, storage, and audit emission.
5. End-to-end tests
   Validate complete banking journeys from upload through final case status, including manual review and escalation paths.
6. Regression tests
   Detect output changes introduced by rule updates, threshold changes, prompt revisions, model replacements, and UI workflow edits.
7. Non-functional tests
   Cover latency, resilience, observability, security control enforcement, and access control behavior.

## 3. Coverage Map

| Area | Must Cover in MVP | Expected Outcome |
| --- | --- | --- |
| Document ingestion | Yes | Accepted files are stored, hashed, scanned, and registered; unsafe files are rejected with reason |
| OCR preprocessing | Yes | Rotation, blur, noise, and contrast handling produces deterministic artifact chain and confidence |
| OCR extraction | Yes | OCR text, line boxes, page refs, and confidence persisted with provenance |
| Document classification | Yes | In-scope docs classified correctly or routed to review when uncertain |
| Field extraction | Yes | Required fields extracted with value, confidence, and evidence reference |
| Validation logic | Yes | Rule failures generate explicit codes and severity |
| Cross-document checks | Yes | Matching and mismatch logic drives pass, warn, or manual review correctly |
| Compliance gates | Yes | Pending checks remain pending; required escalations created |
| Decision engine | Yes | Auto-pass only within approved boundaries; high-risk cases never silently auto-resolve |
| Human review | Yes | Reviewer can correct, comment, escalate, and close with full audit trail |
| Audit logging | Yes | Every significant state change and decision rationale logged immutably |
| Role-based access | Yes | Unauthorized actions blocked and logged |
| Search and case list | Should | Cases visible with correct role-based filters and queue status |
| Reporting and KPI views | Should | Metric calculations match underlying workflow facts |
| Model monitoring | Future | Drift and slice dashboards validated against benchmark baselines |

## 4. Functional Test Areas

### 1. Ingestion Module

| Test Case | Input | Expected Outcome |
| --- | --- | --- |
| Accept valid PDF upload | Single PDF under size limit | Case created, file stored, checksum recorded, audit event emitted |
| Reject unsupported type | Executable renamed as PDF | Upload blocked, reason code `unsupported_or_malicious_file`, no workflow continuation |
| Reject oversized file | File above configured limit | Upload blocked with deterministic API error and audit event |
| Detect duplicate upload | Same checksum uploaded twice to same case | System flags duplicate, preserves both user action and dedupe relationship |
| Partial multi-file upload | Two files valid, one corrupted | Valid files stored; corrupted file rejected; case remains actionable with explicit exception |

### 2. OCR Module

| Test Case | Input | Expected Outcome |
| --- | --- | --- |
| Clean scan OCR | Clear passport image | OCR confidence above target threshold and field text matches golden label |
| Deskew required | Rotated salary slip | Preprocessing corrects rotation, artifact saved, OCR rerun succeeds |
| Low-light image | Dark utility bill photo | OCR confidence drops; case routes to review if key fields unclear |
| Multi-page statement | 6-page bank statement | Page order preserved, page-level OCR stored, missing page detected if absent |
| OCR failure | Corrupted image bytes | Agent returns explicit failure code, retries capped, case moved to review or failed queue |

### 3. Classification Module

| Test Case | Input | Expected Outcome |
| --- | --- | --- |
| Correct statement classification | Standard bank statement | Classified as `bank_statement` with issuer metadata when available |
| Near-neighbor confusion | Salary slip with bank branding | Either correct class or `review_required`; never silent misclassification at low confidence |
| Out-of-scope document | Handwritten letter | Classified as `unknown` and sent to manual review |
| Mixed packet | ID + utility bill + bank statement | Pages/documents segmented and typed correctly, or exception raised |

### 4. Extraction Module

| Test Case | Input | Expected Outcome |
| --- | --- | --- |
| Extract required ID fields | Passport | Name, DOB, ID number, expiry, nationality, document type extracted with evidence refs |
| Missing required field | Utility bill without address | Missing field flagged with hard failure or review code per rules |
| Ambiguous employer name | Salary slip with abbreviated employer | Value extracted with low confidence and normalization candidate, not asserted as exact match |
| Numeric parsing | Statement transactions with commas and negatives | Amounts normalized correctly with locale-safe parsing |
| Multi-value conflict | Two different account numbers appear | Extraction emits conflict, not a single guessed value |

### 5. Validation Module

| Test Case | Input | Expected Outcome |
| --- | --- | --- |
| Expired ID | Passport past expiry | Hard fail code recorded and case blocked from auto-pass |
| Fresh utility bill | Proof of address within allowed age | Passes freshness validation |
| Income threshold mismatch | Salary slip totals do not equal components | Review-needed or fail code generated according to rule severity |
| Address normalization | Minor casing and abbreviation differences | Normalization applied, result recorded as match or near-match consistently |
| Missing consent | Onboarding packet without consent evidence | Compliance pending or fail; case cannot be finalized automatically |

### 6. Compliance Module

| Test Case | Input | Expected Outcome |
| --- | --- | --- |
| All checks complete | KYC case with successful document checks and external screening | Compliance status `completed_pass` only if all required checks present |
| Screening pending | Sanctions adapter timeout | Compliance status remains `pending` or `review_required`; never `completed_pass` |
| PEP hit candidate | Name match with low-confidence hit | Escalation created for analyst review with evidence and screening metadata |
| Incomplete KYC set | Missing proof of address for required jurisdiction | Case blocked from auto-approval |

### 7. Decision Module

| Test Case | Input | Expected Outcome |
| --- | --- | --- |
| High-confidence low-risk packet | Complete onboarding docs, all checks pass | Auto-process allowed only if within approved policy boundary |
| Rule-model disagreement | Validation pass but anomaly score severe | Route to review with disagreement reason code |
| High-risk trigger | Suspected tampering or sanctions candidate | No automatic approval or rejection; escalate |
| Missing evidence | Required field present without evidence ref | Decision blocked; case routes to review or failure |

### 8. Human Review Module

| Test Case | Input | Expected Outcome |
| --- | --- | --- |
| Claim task | Reviewer claims open task | Ownership set, audit event emitted, role enforced |
| Correct extracted field | Reviewer changes DOB after checking image | Correction stored with actor, timestamp, old/new value, rationale |
| Escalate to compliance | Reviewer sees sanctions ambiguity | Escalation created with proper destination queue and reason |
| Close case without authority | Unauthorized reviewer attempts approval | Action denied and logged |

### 9. Audit and Reporting Module

| Test Case | Input | Expected Outcome |
| --- | --- | --- |
| Complete audit reconstruction | Query case history | Timeline includes ingestion, OCR, validation, review, decision, and closure events |
| Missing audit write | Simulated storage failure during state change | State transition blocked or compensating error raised; no silent gap |
| Metric derivation | Set of reviewed and auto cases | STP, review rate, and exception rate match workflow facts exactly |

## 5. Integration Test Areas

### Integration Focus Areas

1. API to persistence
   Expected outcome:
   writes are durable, idempotent, and reflected in case status, audit events, and retrieval endpoints.
2. Workflow to queue
   Expected outcome:
   retries do not duplicate side effects, and each retried step remains traceable by workflow and job identifiers.
3. Queue to AI services
   Expected outcome:
   timeout, failure, malformed-response, and partial-response handling is explicit and visible to operators.
4. Backend to storage
   Expected outcome:
   raw and derived artifacts remain linked to case, document, page, and model/run identifiers.
5. Backend to frontend
   Expected outcome:
   UI shows uncertainty, evidence references, review requirements, and state accurately for each role.
6. Backend to external compliance adapters
   Expected outcome:
   pending, unavailable, and hit statuses are preserved and never flattened into pass.

## 6. End-to-End Workflow Tests

### Core E2E Journeys

1. Retail KYC onboarding, complete packet, auto-review-eligible
   Expected outcome:
   case ingested, docs classified, required fields extracted, validations pass, compliance checks complete, decision allowed only within approved automation boundary, audit complete.
2. Retail KYC onboarding, missing proof of address
   Expected outcome:
   case routes to review, reason code emitted, no final approval.
3. Income verification with clean salary slip and bank statement
   Expected outcome:
   income fields extracted, cross-document consistency checked, final status determined with evidence refs.
4. Income verification with major variance between salary slip and statement credits
   Expected outcome:
   manual review required with variance reason code.
5. Loan intake with unsigned agreement
   Expected outcome:
   fail or review state according to policy, no downstream approval artifact.
6. Fraud-risk document tampering scenario
   Expected outcome:
   escalate to specialist queue, no automated resolution.
7. External dependency degradation
   Expected outcome:
   case remains pending or review-required, retries capped, audit and alert emitted.
8. Reviewer correction and revalidation
   Expected outcome:
   corrected field stored, case revalidated, decision recalculated, full audit preserved.

## 7. Edge-Case Scenarios

| Scenario | Risk | Expected System Behavior |
| --- | --- | --- |
| Blurry phone photo of ID | Wrong identity extraction | Retry preprocessing; if still low confidence, route to manual review |
| Cropped document edges | Missing expiry or ID number | Extract partial fields only; issue missing-field exception |
| Mixed-language document | OCR/extraction ambiguity | Extract recognized text; flag unsupported language risk if required fields uncertain |
| Scanned copy of copy | Low contrast and artifacts | Reduced confidence and likely review routing |
| Password-protected PDF | Inability to inspect | Reject or hold with explicit reason; do not silently skip |
| Duplicate pages in statement | False transaction analysis | Detect duplicate page hash or repeated OCR pattern and flag |
| Missing page in statement | Understated balances or transactions | Exception raised and case blocked from final income or cashflow decision |
| Statement with handwritten notes | Misread annotations as facts | Ignore handwritten overlays unless explicit human review confirms relevance |
| Name variation across docs | False mismatch or false match | Apply normalization rules; near matches go to review |
| Fraudulent alteration | Tampered pay amount or edited PDF text layer | Trigger tampering exception and manual review |
| Two applicants on one upload | Entity confusion | Split case or stop processing with entity ambiguity code |
| OCR text says one value, visual region another | Inconsistent evidence | Route to review; no automatic value selection |
| External screening timeout | False compliant status | Mark compliance pending and prevent final completion |
| Queue redelivery after partial processing | Duplicate actions | Idempotency keys prevent duplicate case mutations |
| Reviewer browser refresh during edit | Lost manual changes | Draft-save or conflict warning; no silent overwrite |

## 8. Low-Quality Document Scenarios

| Scenario | Expected Outcome |
| --- | --- |
| Blurry smartphone capture of passport | OCR artifacts stored, OCR confidence reduced, key fields either extracted with evidence or routed to review |
| Cropped utility bill missing one edge | Partial extraction only; missing-address or missing-date rule fired; no silent pass |
| Shadowed salary slip photo | Image preprocessing attempted; if employer or net pay remains uncertain, manual review required |
| Bank statement with low contrast and faint print | Statement parsing continues only if page completeness and critical totals remain reliable; otherwise blocked |
| Multi-page statement with one unreadable page | Case remains review-required; incomplete financial analysis is not treated as valid |
| PDF scan of photocopy with noise and skew | OCR rerun permitted within retry cap; final route based on confidence and required-field completeness |
| Mixed-language or issuer-variant form | Unsupported fields flagged explicitly; system must not invent normalized values |
| Document with handwritten marks over printed text | Overlay ignored unless human reviewer confirms relevance; conflicting read routes to review |

## 9. Human Review Workflow Tests

1. Review task creation
   Expected outcome:
   review-required cases generate correctly typed tasks with queue, priority, and reason codes.
2. Review task claim and ownership
   Expected outcome:
   only authorized reviewers can claim; ownership and timestamps are audited.
3. Side-by-side evidence review
   Expected outcome:
   reviewer can view source region, extracted value, confidence, and validation outcome without context loss.
4. Manual correction
   Expected outcome:
   old value, new value, actor, rationale, and evidence reference are stored; downstream revalidation triggered.
5. Escalation to specialist queue
   Expected outcome:
   escalation reason, destination role, supporting evidence, and pending status are captured.
6. Unauthorized manual action attempt
   Expected outcome:
   forbidden action blocked with clear error and audit record.
7. Review completion and closeout
   Expected outcome:
   only allowed roles can approve, reject, or close according to policy gates and pending-check status.

## 10. Security-Sensitive Behavior Tests

1. Malicious file upload
   Expected outcome:
   executable or malformed payload rejected, quarantined as required, and logged without further processing.
2. Unauthorized document access
   Expected outcome:
   access denied by role and case scope; denial event captured.
3. Unauthorized workflow action
   Expected outcome:
   user without required role cannot approve, reject, escalate, or retrieve sensitive audit details.
4. Secret or token leakage prevention
   Expected outcome:
   logs, API errors, and UI surfaces do not expose secrets, raw credentials, or sensitive internal endpoints.
5. Audit tamper resistance
   Expected outcome:
   critical audit events cannot be silently overwritten or deleted through normal application paths.
6. Queue redelivery with duplicate side effects
   Expected outcome:
   no duplicate final decision, no duplicate review task, and no duplicate audit closeout event.
7. External adapter timeout or spoofed response
   Expected outcome:
   compliance status remains pending or review-required until verified result is available.

## 11. Regression Strategy

### Regression Scope

1. Business rules
   Any change to required fields, validation thresholds, matching logic, or review routing.
2. Models
   Any change to OCR, classification, extraction, anomaly, or confidence models.
3. Prompts
   Any prompt text, output schema, tool policy, model provider, or confidence-language change.
4. APIs and contracts
   Any schema, enum, workflow state, reason code, or event payload change.
5. UI workflows
   Any change to correction, escalation, approval, rejection, or audit-view behavior.

### Regression Packs

1. Golden case pack
   Stable fixtures with approved expected outputs for each in-scope document type.
2. Messy case pack
   Low-quality scans, issuer variants, partial packets, altered docs, and contradictory evidence.
3. Safety case pack
   Cases specifically designed to ensure high-risk automation does not occur.
4. Audit pack
   Cases verifying event completeness, reproducibility, and evidence linkage.
5. Access-control pack
   Role/permission scenarios across allowed and denied actions.

### Regression Rules

1. No model, prompt, or rule change may ship without before/after benchmark comparison.
2. Any change that increases false auto-pass on safety cases is a release blocker.
3. Threshold changes require documented rationale and QA sign-off.
4. Regression results must be stored with version identifiers for rule set, prompt set, and model set.

## UAT Checklist

### Operations User Acceptance

1. Branch or ops user can create a case and upload documents without training on internal system details.
2. Case list clearly shows status, owner, aging, and review priority.
3. Reviewer can compare extracted fields against source evidence without opening separate tools.
4. Reviewer can correct fields, add notes, and escalate with minimal clicks.
5. Reason codes are understandable and operationally meaningful.

### Compliance User Acceptance

1. Compliance analyst can see which checks are completed, pending, or failed.
2. Pending external checks are visually distinct from pass states.
3. Escalation packages include enough evidence to act without re-building context manually.
4. Audit timeline is complete and exportable for investigation.

### Risk and Control Acceptance

1. No high-risk case is auto-approved.
2. All final decisions show rationale, evidence references, and actor or system source.
3. Role restrictions prevent unauthorized closure, approval, or override actions.
4. Sensitive data exposure in UI and logs is limited to authorized users only.

### Product Acceptance

1. MVP document types behave according to the PRD and banking-rule documents.
2. KPI calculations reflect actual workflow events.
3. Exception queues are usable and not overloaded by avoidable false positives.

## 12. MVP Release Gate

### Must Pass Before MVP Release

1. All P0 and P1 defects closed.
2. No known path exists for silent high-risk auto-approval or silent compliance bypass.
3. All in-scope E2E journeys pass in staging.
4. Audit completeness tests pass for create, upload, process, review, escalate, revalidate, and close flows.
5. Access-control tests pass for all high-privilege actions.
6. Regression pack shows no unapproved degradation on:
   OCR field accuracy, extraction accuracy, review rate, false auto-pass rate, and exception routing correctness.
7. Retry and failure tests confirm visible failure states and capped retries.

### Quantitative Gates for MVP

1. API contract test pass rate: 100 percent for supported endpoints.
2. Workflow state transition invalid-transition rejection: 100 percent.
3. Evidence-link completeness for required extracted fields: 100 percent in golden and UAT packs.
4. Audit event completeness for critical actions: 100 percent.
5. False auto-pass rate on safety-case pack: 0 percent.
6. Manual review routing precision on predefined review-required pack:
   high enough that no severe known review-required case is auto-processed.

## 13. Scale-Stage Test Evolution

### Beta and Scale Gates

1. Load tests for target concurrency and document volume pass with no data loss.
2. Disaster recovery restore test proves case, evidence, and audit recoverability.
3. Production-shadow benchmark confirms no material drift before enabling broader automation.
4. Periodic re-certification of prompts, models, and thresholds completed with archived results.

## Data and Fixture Strategy

### Required Test Data Sets

1. Clean golden set
   Small but exact reference set for every MVP document type.
2. Messy real-world set
   Blurry, skewed, low-contrast, cropped, partial, multi-page, mixed-template, and annotation-heavy variants.
3. Adversarial set
   Tampered values, swapped pages, fake statements, malicious files, and contradictory evidence packs.
4. Workflow set
   Synthetic cases designed to drive escalation, rejection, revalidation, duplicate upload, and retry conditions.

### Data Controls

1. Use only synthetic or properly sanitized documents.
2. Every fixture must have:
   source label, document type, expected fields, expected validation outcomes, expected case route, and expected audit events.
3. Any production-derived sample used for test improvement must pass privacy review and de-identification checks.

## Automation Recommendations

1. Run unit, contract, and core integration tests on every pull request.
2. Run golden-pack regression on every merge to main.
3. Run messy-pack, safety-pack, and E2E suites nightly and before release candidate sign-off.
4. Run prompt and model comparison suites whenever prompt/model versions change.
5. Publish QA scorecards with:
   pass rate, blocked tests, defect severity mix, regression deltas, and unresolved release risks.

## Defect Prioritization Policy

| Severity | Description | Release Impact |
| --- | --- | --- |
| P0 | Wrong approval, wrong rejection, compliance bypass, missing audit trail, unauthorized access, data loss | Immediate release block |
| P1 | Incorrect review routing, incorrect required field extraction on common path, broken escalation, retry storm risk | Release block unless explicitly waived by governance |
| P2 | Non-critical UI issue, minor metric mismatch, low-frequency template issue with fallback | Fix before broad rollout or track in beta |
| P3 | Cosmetic issue or low-impact usability issue | Does not block release |

## Exit Criteria for QA Sign-Off

QA recommends release only when:

1. all critical banking workflows are test-passed;
2. high-risk automation boundaries are enforced in test;
3. evidence and audit traceability are complete;
4. known residual issues are documented, accepted, and non-safety-critical; and
5. UAT stakeholders from operations, compliance, and product have signed off on the MVP scope.

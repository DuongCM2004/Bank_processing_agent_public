# Compliance and Risk Controls for Ops Agent

## 1. Scope and Regulatory Baseline

This document defines the minimum compliance, audit, and governance controls for the banking Document Processing Agent ("Ops Agent"). It is written as a conservative U.S.-bank baseline for internal operations workflows that support KYC, AML, onboarding, and lending document intake.

The control posture assumes:

1. Regulators, internal audit, model risk management, and external auditors may inspect the system.
2. AI-assisted outputs are advisory unless an approved policy explicitly permits automation.
3. Compliance status must always distinguish completed checks from pending checks.
4. High-risk automation must never occur silently.

This control set is designed to align operationally with current U.S. supervisory expectations, including:

1. Customer Identification Program and identity verification recordkeeping under 31 CFR 1020.220 and FFIEC BSA/AML examination guidance.
2. Risk-based customer due diligence and suspicious activity escalation principles reflected in FFIEC and FinCEN guidance.
3. Model risk governance and independent validation principles in Federal Reserve / OCC SR 11-7.
4. Trustworthy AI governance concepts from NIST AI RMF 1.0 and the July 26, 2024 Generative AI Profile.

## 2. Compliance Control Matrix

| Control ID | Control area | Objective | Requirement | Evidence required | Automation boundary | Owner |
|---|---|---|---|---|---|---|
| CCM-01 | Customer identification | Ensure required identifying information is collected before account-opening workflow proceeds | For individual onboarding, collect and retain name, date of birth, address, and identification number before completion of regulated intake | Case payload, extracted fields, source document refs, timestamp | Can collect and prefill automatically; cannot mark complete if required fields missing | Ops + Compliance |
| CCM-02 | Identity verification | Form a reasonable belief in customer identity | System must record documentary and non-documentary verification results separately and identify unresolved discrepancies | Verification method, document details, discrepancy notes | AI may recommend; human approval required when discrepancy exists | Compliance |
| CCM-03 | Document completeness | Prevent incomplete regulated packs from progressing | Workflow-specific required documents must be present before case can be marked compliant-ready | Required-doc checklist status | No auto-pass if any required doc missing | Ops |
| CCM-04 | OFAC / sanctions gating | Prevent opening or progressing restricted cases without review | Any sanctions, PEP, adverse media, or law-enforcement hold signal must create a specialist review gate | Screening result ref, screening timestamp, watchlist/version | Never auto-clear true or possible matches | Compliance |
| CCM-05 | AML / suspicious activity referral | Ensure suspicious indicators are escalated | Identity inconsistency, suspected manipulation, unusual document patterns, or linked transaction red flags must route for investigation | Alert record, reasons, evidence refs, investigator assignment | Never auto-close suspicious activity cases | Fraud / AML |
| CCM-06 | Beneficial ownership / legal entity review | Ensure legal-entity workflows meet due diligence requirements | For legal entity customers, record beneficial owner / control-person data requirements applicable to the workflow and date-specific policy | Entity data, control persons, verification notes | No auto-approval for legal entity ownership review in current scope | Compliance |
| CCM-07 | Explainability | Make AI-assisted outputs reviewable | Each extraction, classification, and validation output must include reason code, confidence, and evidence reference | Model output payload, prompt/model version, evidence refs | No hidden scoring | Product + Engineering |
| CCM-08 | Human review gating | Prevent unsafe automation | High-risk, ambiguous, or policy-exception cases must stop for human action | Review task, assignee, decision note, rationale | Mandatory human action for all gated cases | Ops + Compliance |
| CCM-09 | Audit trail immutability | Support examination and reconstruction | All material events must be append-only, time-stamped, actor-attributed, and queryable by case | Audit event log | No delete or overwrite in production | Engineering |
| CCM-10 | Record retention | Preserve required records for review and legal holds | Retain CIP and supporting verification records for at least required periods; support legal hold extension | Retention metadata, storage location, hold flags | Retention may be automated; purge must honor hold rules | Compliance + Records |
| CCM-11 | Segregation of duties | Prevent self-approval and unmanaged overrides | Users who configure models/rules/prompts must not independently approve production use of those changes | Change approval records, role map | No self-approval for high-impact changes | Risk + Engineering |
| CCM-12 | Model governance | Control model and prompt changes | Any material model, threshold, or prompt change must be versioned, tested, approved, and rollback-capable | Change ticket, test results, approval, deployment record | No unapproved production prompt/model changes | Model Risk + Engineering |
| CCM-13 | Independent testing | Support auditability and compliance assurance | Periodic independent testing must assess control design and operating effectiveness | Audit reports, test cases, findings | Cannot be performed by control owners alone | Internal Audit |
| CCM-14 | Pending check visibility | Distinguish complete vs incomplete control state | System UI and API must expose each check as pass, fail, pending, not_applicable, or review_required | Check registry per case | Cases with pending critical checks cannot be treated as compliant | Engineering + Product |
| CCM-15 | Exception management | Ensure deviations are traceable and approved | Any override, waiver, or exception must include approver, rationale, policy reference, and expiry if temporary | Exception record | No silent override | Compliance |

## 3. Human Review Control Policy

## 3.1 Decisions that may be automated

These may be automated only if all prerequisite controls pass and the workflow has explicit approval for straight-through processing:

1. Document type classification for supported low-risk document types.
2. Field extraction and normalization.
3. Deterministic completeness checks.
4. Deterministic freshness checks.
5. Deterministic format and pattern checks.
6. Queue assignment for low-risk operational review.
7. Recommendation that a case is "eligible for straight-through processing" for low-risk retail segments.

Automation is acceptable only when the system also records:

1. the checks performed,
2. the evidence used,
3. the confidence or rule result,
4. the policy version applied,
5. the fact that the case was auto-routed.

## 3.2 Decisions that require human approval

Human approval is mandatory for:

1. Final KYC approval in the initial release.
2. Any case involving sanctions, PEP, or adverse-media concern.
3. Any possible suspicious activity or suspected document manipulation.
4. Any identity discrepancy that is not fully resolved by deterministic rules.
5. Any rejection outcome for onboarding or lending intake.
6. Any policy exception or override.
7. Any material correction to identity, DOB, address, or income values.
8. Any legal-entity / beneficial-ownership review.
9. Any escalated case.
10. Any case with one or more critical checks still pending.

## 3.3 Decisions that must never be automated silently

The system must never silently:

1. suppress a sanctions or AML alert,
2. change a compliance status from review-required to compliant without a recorded decision path,
3. overwrite original extracted values,
4. downgrade exception severity without a versioned rules change or authorized override,
5. close a case with unresolved critical compliance checks.

## 4. Compliance Status Model

Each case must maintain a compliance control status separate from operational workflow status.

### 4.1 Status definitions

| Status | Meaning | Allowed progression |
|---|---|---|
| `pending` | Check not yet executed or result unavailable | Must remain pending until evaluated |
| `completed_pass` | Check completed and passed | Can support downstream progression |
| `completed_fail` | Check completed and failed | Must block or route according to severity |
| `review_required` | Check result exists but requires human judgment | Must not be treated as compliant |
| `partial_compliance` | Some required controls passed, but one or more required controls remain pending or unresolved | May remain in queue; cannot be represented as fully compliant |
| `non_compliant` | Required control failed or required evidence absent | Must block completion until resolved or formally rejected |

### 4.2 Control-state definitions for reporting

#### Compliant

All required controls for the workflow are in `completed_pass`, no critical check is pending, and no unresolved review-required condition remains.

#### Partially compliant

Some required controls have passed, but at least one required control is still pending, or a non-critical review item remains open.

#### Review needed

At least one required control cannot be concluded by deterministic logic, or a high-risk indicator requires human judgment.

#### Non-compliant

A required control failed, a required document is missing, evidence is insufficient, or a prohibited condition exists.

The system must never map `pending`, `partial_compliance`, or `review_required` to "approved" or "compliant" in external-facing outputs.

## 5. Risk Escalation Rules

## 5.1 Mandatory escalation triggers

| Trigger | Severity | Queue | Required action |
|---|---:|---|---|
| Date of birth mismatch across identity and application | Critical | Compliance / Fraud | Stop workflow, investigate, record disposition |
| Suspected document alteration or tampering | Critical | Fraud | Fraud analyst review only |
| Possible sanctions / PEP / adverse media match | Critical | Compliance | Specialist review before any progression |
| Identity document expired | High | Operations / Compliance | Request new document or reject per policy |
| Missing beneficial ownership information where required | High | Compliance | Block legal-entity progression |
| Material name mismatch with no approved alias basis | High | Compliance | Investigate and document |
| Missing consent for regulated checks | High | Operations / Compliance | Block downstream checks |
| Salary / income mismatch above hard-fail tolerance | High | Lending Ops / Risk | Investigate or reject |
| Incomplete statement period for required analysis | High | Ops | Request additional documents |
| Low-confidence extraction on critical identity fields | Medium to High | Ops review | Human correction or resubmission |

## 5.2 Escalation handling requirements

For every escalation, the system must capture:

1. escalation trigger,
2. source event,
3. severity,
4. queue or target team,
5. assigned reviewer,
6. reason code,
7. evidence refs,
8. timestamp,
9. final disposition.

Escalated cases must not be auto-closed. Resolution requires a named human actor.

## 6. Audit Logging Requirements

## 6.1 Minimum auditable events

The system must log at minimum:

1. case creation,
2. document upload and replacement,
3. document classification result,
4. field extraction result,
5. validation rule execution,
6. confidence scores and threshold outcomes,
7. queue assignment,
8. human task claim,
9. field correction,
10. revalidation,
11. escalation,
12. sanctions / AML / fraud alert creation,
13. close decision,
14. any override or waiver,
15. model version, prompt version, rules version, and deployment version used for the case.

## 6.2 Required fields for every audit event

Every audit event must contain:

1. unique event ID,
2. case ID,
3. resource type,
4. resource ID,
5. action type,
6. actor type: system or user,
7. actor ID or service ID,
8. occurred-at timestamp in UTC,
9. immutable event payload,
10. prior state and new state where applicable,
11. request or correlation ID,
12. source channel.

## 6.3 Explainability and evidence logging for AI-assisted steps

For any AI-assisted classification, extraction, or recommendation, log:

1. model name and version,
2. prompt template ID and version,
3. retrieval or rules context version if used,
4. confidence output,
5. evidence refs used for the conclusion,
6. normalized output,
7. raw output snapshot or equivalent reproducible artifact,
8. post-processing rules applied,
9. final surfaced result,
10. human override if later changed.

If a result cannot be explained with stored evidence and versioned logic, it must not support a compliance-sensitive automated decision.

## 6.4 Retention requirements

Using FFIEC / BSA recordkeeping as the baseline:

1. CIP identifying information must be retained for at least five years after account closure.
2. Identity verification methods, documentary references, and discrepancy resolution records must be retained for at least five years after the record is made.
3. SAR-related supporting documentation must be retained for at least five years from filing.
4. Audit logs, override records, and model/prompt decision artifacts for regulated workflows should be retained at least as long as the underlying compliance record, and longer if legal hold, investigation, or litigation hold applies.
5. Purge jobs must be legal-hold aware and approval-gated for regulated data classes.

## 7. AI Usage Boundary Document

## 7.1 Permitted AI usage

AI may be used to:

1. classify documents,
2. extract fields,
3. normalize formats,
4. suggest exception reason codes,
5. recommend routing,
6. summarize review history for human reviewers.

These uses are permitted only when:

1. the output is versioned and logged,
2. confidence or abstention behavior exists,
3. deterministic post-checks validate critical fields,
4. humans can inspect source evidence,
5. the system can reproduce which logic version produced the output.

## 7.2 Prohibited AI usage

AI must not:

1. make final sanctions, AML, fraud, or suspicious-activity determinations,
2. make final adverse onboarding or lending rejection decisions,
3. bypass missing-document or missing-consent requirements,
4. invent or infer absent customer identity data without evidence,
5. suppress alerts because of model confidence alone,
6. change retention, audit, or severity policies dynamically without approved governance.

## 7.3 Required model behavior controls

Prompts and model wrappers must enforce:

1. abstain when evidence is insufficient,
2. return structured outputs only,
3. separate observed facts from inferred conclusions,
4. cite evidence refs for every material field,
5. emit explicit uncertainty,
6. avoid unsupported completion of missing values,
7. preserve source-text ambiguity where it exists.

## 8. Governance for Model Updates and Prompt Changes

## 8.1 Change classification

Treat the following as governed changes:

1. base model change,
2. prompt template change,
3. extraction schema change,
4. confidence threshold change,
5. validation-rule change,
6. post-processing logic change,
7. queue-routing logic change,
8. evidence-selection logic change.

## 8.2 Required pre-production controls

Before production deployment of a governed change:

1. document the change objective and expected impact,
2. assign version ID,
3. run benchmark testing on representative banking documents,
4. compare precision, recall, false-accept, false-reject, and abstention rates,
5. test high-risk scenarios and edge cases,
6. obtain control-owner approval,
7. obtain independent validation or challenge for material changes,
8. confirm rollback plan,
9. update runbooks and reviewer guidance if behavior changes.

## 8.3 Production controls

In production:

1. deploy through approved release workflow only,
2. monitor drift and exception-rate change,
3. monitor override rate and escalation rate after change,
4. support version rollback,
5. block emergency prompt changes unless break-glass approval is recorded.

## 8.4 Independent challenge and validation

For material changes affecting regulated decisions:

1. validation must be performed by a function independent from model development,
2. validation must test conceptual soundness, implementation correctness, and ongoing performance,
3. validation conclusions and known limitations must be documented,
4. unresolved high-severity findings must block production release.

## 9. Prompt, Workflow, and Model Control-Gap Review

## 9.1 Control gaps that must be closed

Based on the current Ops Agent workflow foundation, these controls are still required before regulated production use:

1. authentication and role-based authorization enforcement,
2. immutable production-grade audit storage,
3. OCR / model adapter governance and version tracking,
4. explicit compliance-check registry with pass/fail/pending status,
5. sanctions / AML / fraud integration points,
6. document retention and legal-hold controls,
7. reviewer UI showing evidence-backed explanations,
8. override / waiver approval workflow,
9. independent testing and control monitoring.

## 9.2 Prompt-level gaps to avoid

Prompts are non-compliant if they:

1. ask the model to "decide approval" without requiring evidence-backed rationale,
2. ask the model to guess missing regulated fields,
3. do not require explicit uncertainty handling,
4. do not return machine-readable reason codes,
5. do not store prompt version and context used.

## 9.3 Workflow decision gaps to avoid

Workflow design is non-compliant if it:

1. treats extraction success as identity verification,
2. conflates "pending" with "passed",
3. allows case closure before critical checks complete,
4. lets the same actor both configure and approve a material rules change,
5. allows escalated cases to be resolved without documented human rationale.

## 10. Minimum Implementation Requirements Before Pilot

Before any pilot touching real regulated workflows, the system should have at least:

1. role-based access control,
2. append-only audit events with query capability,
3. compliance-check status model,
4. versioned model/prompt/rule tracking,
5. human review gates for all high-risk decisions,
6. retention metadata and legal-hold support,
7. override logging,
8. documented escalation playbooks,
9. benchmarked extraction quality for in-scope document types,
10. sign-off from Compliance, Risk, and Engineering.

## 11. Source Notes

This document was written using primary-source references current as checked on April 14, 2026. Key source anchors:

1. FFIEC BSA/AML Manual, Customer Identification Program and examination procedures: [FFIEC CIP](https://bsaaml.ffiec.gov/manual/AssessingComplianceWithBSARegulatoryRequirements/01)
2. FFIEC CIP examination procedures and required identifying information / discrepancy handling: [FFIEC CIP Examination Procedures](https://bsaaml.ffiec.gov/manual/AssessingComplianceWithBSARegulatoryRequirements/01_ep)
3. FFIEC BSA record retention summary, including CIP and SAR support: [FFIEC Appendix P](https://bsaaml.ffiec.gov/manual/Appendices/17)
4. FFIEC Suspicious Activity Reporting guidance: [FFIEC SAR](https://bsaaml.ffiec.gov/manual/AssessingComplianceWithBSARegulatoryRequirements/04)
5. Federal Reserve / OCC supervisory guidance on model risk management: [SR 11-7](https://www.federalreserve.gov/supervisionreg/srletters/sr1107a1.pdf)
6. FinCEN CDD rule overview and February 13, 2026 exceptive relief note for certain beneficial ownership re-verification requirements: [FinCEN CDD Final Rule](https://www.fincen.gov/index.php/resources/statutes-and-regulations/cdd-final-rule)
7. NIST AI Risk Management Framework: [NIST AI RMF 1.0](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10)
8. NIST Generative AI Profile, published July 26, 2024: [NIST AI RMF GenAI Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence)

Where this document makes implementation recommendations beyond those sources, it does so as a conservative banking control inference rather than as a direct regulatory mandate.

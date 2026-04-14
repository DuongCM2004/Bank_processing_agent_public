# Banking Document Rules for Ops Agent

## 1. Purpose

This document translates banking operations practice into implementation-grade rules for document intake, extraction, validation, exception handling, and decision routing. It is intended for product, engineering, operations, compliance, and QA teams building the Ops Agent.

The core design principle is simple: a document is only useful if it is operationally decisionable. Extraction quality alone is not enough. A document must also be complete, current, internally consistent, and consistent with the rest of the case.

## 2. Banking Document Taxonomy

### 2.1 Category hierarchy

| Category | Document type | Primary banking purpose | Typical workflow |
|---|---|---|---|
| Identity | National ID card | Verify legal identity | KYC onboarding, loan application |
| Identity | Passport | Verify legal identity and nationality | KYC onboarding, high-value account opening |
| Identity | Driver's license | Supplemental identity | Retail onboarding, lending |
| Address | Utility bill | Verify residential address | KYC onboarding, account maintenance |
| Address | Government address letter | Verify residential address | KYC onboarding |
| Address | Bank-issued address letter | Verify residential address | KYC onboarding |
| Income | Salary slip / payslip | Verify recurring employment income | Income verification, loan underwriting |
| Income | Employment letter / salary certificate | Verify employer, role, and declared salary | Income verification, loan underwriting |
| Banking | Bank statement | Verify account ownership, cash flow, and salary credit | Income verification, affordability |
| Lending | Loan application form | Capture declared applicant data and requested facility | Loan intake |
| Lending | Loan agreement | Record executed lending contract terms | Post-approval fulfillment, audit |
| Commercial | Invoice | Verify trade/commercial claim or payable support | Trade finance, SME review |
| Commercial | Purchase order / delivery support | Validate commercial relationship and goods flow | Trade finance |
| Corporate | Certificate of incorporation | Verify legal entity existence | Corporate onboarding |
| Corporate | Business registration / tax registration | Verify registered entity details | Corporate onboarding |
| Corporate | Articles / operating document | Verify governance structure | Corporate onboarding |
| Corporate | Shareholder / beneficial ownership declaration | Verify ownership and control | Corporate KYC |

### 2.2 MVP vs extended scope

#### Must-have for first banking release

1. National ID card
2. Passport
3. Driver's license
4. Utility bill
5. Bank-issued address letter
6. Salary slip / payslip
7. Employment letter / salary certificate
8. Bank statement
9. Loan application form
10. Basic signed consent form

#### Should-have next

1. Government address letter
2. Loan agreement
3. Certificate of incorporation
4. Tax registration document
5. Basic invoice review

#### Future

1. Full corporate ownership packs
2. Trade-finance document sets
3. Jurisdiction-specific tax filings

## 3. Field Requirement Matrix

### 3.1 Identity documents

| Document type | Required fields | Optional but useful fields | Operational note |
|---|---|---|---|
| National ID card | full_name, date_of_birth, document_number, expiry_date if present on card, issuing_country, sex if shown | nationality, place_of_birth, issue_date | If card has no expiry by design, issuer rule must allow null expiry |
| Passport | full_name, date_of_birth, passport_number, nationality, expiry_date, issuing_country | sex, place_of_birth, issue_date, MRZ lines | MRZ and visual zone should be cross-checked when available |
| Driver's license | full_name, date_of_birth, license_number, expiry_date, issuing_state_or_country | address_on_license, issue_date, class | License is weaker than passport in many policies; use according to product policy |

### 3.2 Address documents

| Document type | Required fields | Optional but useful fields | Operational note |
|---|---|---|---|
| Utility bill | customer_name, address_line_1, statement_or_issue_date, issuer_name | account_number, service_address, address_line_2, postal_code | Must show service provider or official issuer clearly |
| Government address letter | customer_name, address_line_1, issue_date, issuing_authority | postal_code, address_line_2 | Higher trust than private correspondence |
| Bank-issued address letter | customer_name, address_line_1, issue_date, bank_name | account_reference | Accept only if issued by regulated bank and date is visible |

### 3.3 Income documents

| Document type | Required fields | Optional but useful fields | Operational note |
|---|---|---|---|
| Salary slip / payslip | employee_name, employer_name, pay_period_start_or_label, pay_period_end_or_label, net_pay or gross_pay, payment_date if shown | tax_deductions, allowances, employee_id, currency, YTD totals | Net pay preferred for affordability; gross pay still useful |
| Employment letter / salary certificate | employee_name, employer_name, employment_status, issue_date, salary_amount, salary_frequency, authorized_signatory if shown | role_title, start_date, HR contact | Weak if unsigned, undated, or generic template with no employer identity |

### 3.4 Banking documents

| Document type | Required fields | Optional but useful fields | Operational note |
|---|---|---|---|
| Bank statement | account_holder_name, account_number_masked_or_full, statement_start_date, statement_end_date, bank_name | opening_balance, closing_balance, transaction_rows, salary_credit_candidates, branch_name | Digital statements preferred; scanned images have lower automation confidence |

### 3.5 Lending documents

| Document type | Required fields | Optional but useful fields | Operational note |
|---|---|---|---|
| Loan application form | applicant_name, requested_loan_amount, declared_income, address, contact_number, product_type, signature_present | employer_name, co-applicant, term, purpose, submission_date | Signature requirement depends on channel and policy |
| Loan agreement | borrower_name, facility_amount, interest_rate, term, execution_date, agreement_number, signature_present | repayment_schedule, collateral_ref, co-borrower | Not an intake document in early automation phases |
| Consent form | applicant_name, consent_type, execution_date, signature_present | channel, reference_number | Missing consent is a hard stop for regulated downstream checks |

### 3.6 Commercial and corporate documents

| Document type | Required fields | Optional but useful fields | Operational note |
|---|---|---|---|
| Invoice | supplier_name, buyer_name, invoice_number, invoice_date, invoice_amount, currency | PO_number, tax_amount, due_date, line_items | Invoice alone should not drive funding decisions without supporting docs |
| Certificate of incorporation | legal_entity_name, registration_number, incorporation_date, issuing_jurisdiction | registered_address | Core corporate existence proof |
| Tax registration document | legal_entity_name, tax_number, issuing_authority, issue_or_effective_date | registered_address | Jurisdiction-specific format rules required |
| Beneficial ownership declaration | legal_entity_name, owner_name_list, ownership_percentages, declaration_date | controller_role | Never auto-approve without specialist review |

## 4. Validation Rules Catalog

## 4.1 General document-level rules

### Hard fail

1. File cannot be opened or parsed.
2. File is password-protected and no approved decryption flow exists.
3. Document type is unsupported for the workflow.
4. Document is blank, truncated, or materially unreadable.
5. Mandatory issuer or customer identity area is missing.

### Manual review

1. Low image quality but some fields are readable.
2. Multi-page document with one low-quality page but not all content lost.
3. Possible duplicate document within case.
4. Uncertain classification between two close document types.

### Soft warning

1. Non-critical optional fields missing.
2. Minor OCR noise where high-confidence correction is available.

## 4.2 Major field validation logic

| Field | Validation logic | Hard fail | Manual review | Soft warning |
|---|---|---|---|---|
| full_name | Must be non-empty, alphabetic pattern allowed with punctuation, normalized for case and spacing | Missing on identity doc | Partial name, initials only, OCR uncertainty | Minor accent/spacing normalization |
| date_of_birth | Must parse to valid past date; age may be checked against product policy | Missing on primary ID | Ambiguous format or partial date | None |
| document_number | Must be non-empty and match issuer-specific or generic pattern | Missing on primary ID | Pattern uncertain but legible | Format differs but still plausible |
| expiry_date | Must parse as date; compare to case submission date | Expired when policy requires valid doc | Near expiry inside review window | Expiring soon warning |
| issuing_country / authority | Must be present for ID/passport | Missing on passport | Low-confidence issuer extraction | None |
| address_line_1 | Must be present on address proof | Missing on address proof | Address visible but fragmented | Missing postal code only |
| issue_date / statement date | Must be parseable and within freshness window | Missing when freshness required | Date ambiguous but likely valid | Slightly stale but policy allows warning |
| employer_name | Must be present on income docs | Missing on payslip or employment letter | Abbreviated or logo-only employer | Minor normalization |
| income_amount | Must parse numeric and currency | No pay amount on payslip | Multiple candidate values and unclear net/gross | Gross only when net preferred |
| statement_period | Start and end date must be parseable and ordered correctly | Missing period | One boundary date unclear | Period shorter than preferred but still usable |
| account_holder_name | Must be present on statement | Missing | Business/personal naming ambiguity | Formatting variance only |
| requested_loan_amount | Must parse positive numeric amount | Missing on application | Handwritten correction or multiple amounts | None |
| signature_present | Detect visible signature or approved e-sign mark | Required signature absent | Mark unclear | Signature not required for that channel |

## 4.3 Document validity windows

| Document type | Freshness / validity standard | Rule class |
|---|---|---|
| Passport | Must not be expired on submission date; near-expiry window of 90 days should trigger review if policy requires durable validity | Hard fail if expired; manual review if near expiry |
| National ID card | Must not be expired where expiry exists | Hard fail if expired |
| Driver's license | Must not be expired if used as accepted ID | Hard fail if expired |
| Utility bill | Issue date should be within 90 days unless jurisdiction policy differs | Hard fail if older than policy and no override allowed; manual review if date is unclear |
| Bank-issued address letter | Usually within 90 days | Same as above |
| Payslip | Usually within last 60 days; most recent payslip preferred | Manual review if slightly stale; hard fail if materially old for workflow |
| Employment letter | Usually within 30 to 90 days depending policy | Manual review if older than threshold unless employer relationship confirmed elsewhere |
| Bank statement | Usually last 1 to 3 months depending product | Hard fail if required coverage period not met |
| Loan application form | Must be current version and signed where required | Hard fail if unsigned or obsolete form if policy mandates current version |
| Consent form | Must be signed and current for required checks | Hard fail |

## 5. Cross-Document Matching Rules

## 5.1 Identity consistency

### Hard fail

1. Primary identity document full name materially conflicts with loan application applicant name and no documented alias logic exists.
2. Date of birth on primary identity document conflicts with onboarding record or application.
3. Passport / ID number conflicts across two supposed copies of the same identity document.

### Manual review

1. Minor name variation due to initials, middle names, spacing, transliteration, or marital name change.
2. Address document name matches surname and initials but not full expansion.
3. One document shows truncated names due to issuer formatting.

### Matching standard

1. Normalize case, punctuation, repeated spaces, and common honorifics.
2. Compare legal name tokens.
3. Support alias table only if bank policy explicitly permits it.
4. Treat date of birth as exact match field after format normalization.

## 5.2 Address consistency

### Hard fail

1. Proof-of-address shows clearly different residence than declared application address and the product requires current residential address match.

### Manual review

1. Apartment/unit missing in one source only.
2. Common street abbreviation differences.
3. Postal code missing in one source.
4. Service address differs from mailing address on utility bill.

### Matching standard

1. Normalize street abbreviations, punctuation, casing, and unit markers.
2. Compare house/building number, street root, city, and postal code.
3. Require exact or near-exact match on core address elements for auto-pass.

## 5.3 Income consistency

### Hard fail

1. Declared monthly income on loan application materially exceeds verified payslip income above tolerance.
2. Employer name on employment letter and payslip are clearly different with no corporate alias justification.

### Manual review

1. Gross pay matches but net pay differs because of deductions.
2. Salary credit appears in statement under payroll processor name rather than employer name.
3. Salary amount varies due to overtime, bonus, or partial month.

### Matching standard

1. Compare pay frequency first: monthly, biweekly, weekly.
2. Normalize verified income to monthly equivalent before comparing to declared amount.
3. Default material variance tolerance for auto-pass: 10%.
4. Variance above 10% and up to 20% should route to review.
5. Variance above 20% is hard fail unless override policy exists.

## 5.4 Banking consistency

### Hard fail

1. Account holder name on statement does not correspond to applicant or documented joint account holder where the workflow requires applicant-owned account.
2. Statement period coverage is materially shorter than policy minimum.

### Manual review

1. Salary credits cannot be clearly identified because descriptors are abbreviated.
2. Joint account statement includes applicant but also another holder.
3. Scanned statement quality prevents reliable transaction parsing.

## 6. Exception Handling Guide

## 6.1 Standard exception scenarios

| Exception code | Description | Severity | Standard ops action |
|---|---|---:|---|
| unreadable_document | Document content materially unreadable | High | Request resubmission |
| unsupported_document_type | Document not supported for workflow | High | Route to manual review or request correct document |
| expired_id_document | Primary ID expired | High | Reject or request valid replacement |
| stale_address_proof | Address proof older than policy threshold | High | Request newer address proof |
| missing_mandatory_field | Required field not extracted or absent | High | Manual review; request replacement if truly absent |
| low_confidence_field | Required field extracted below threshold | Medium | Manual review and correction |
| cross_document_name_mismatch | Name mismatch across docs | High | Compliance review |
| cross_document_dob_mismatch | DOB mismatch across docs | Critical | Compliance or fraud review |
| income_variance | Declared vs verified income outside tolerance | Medium to High | Review and document rationale |
| employer_mismatch | Employer data conflicts | High | Manual review; request clarification |
| duplicate_document | Same or near-same document resubmitted | Medium | Confirm intent; ignore duplicate or escalate |
| suspected_manipulation | Document appears altered or inconsistent | Critical | Fraud review only |
| missing_signature | Required signature absent | High | Request signed form |
| incomplete_statement_period | Statement does not cover required period | High | Request additional statements |
| no_salary_evidence | Expected salary credit not visible in bank statement | Medium | Review with applicant explanation or alternate proof |

## 6.2 Operational handling model

### Request resubmission

Use when the source document itself is not operationally usable:

1. unreadable scans
2. expired identity document
3. stale proof of address
4. incomplete bank statement coverage
5. missing signed consent

### Manual correction and continue

Use when the underlying document is acceptable but extraction is imperfect:

1. low-confidence field
2. OCR split of name or address lines
3. one missing non-critical value that reviewer can reliably confirm

### Specialist escalation

Use when the issue is risk-sensitive and not just a data quality problem:

1. identity mismatch
2. DOB mismatch
3. suspected manipulation
4. inconsistent signatures
5. sanctions or fraud-related flags from upstream systems

## 7. Operational Decision Logic

## 7.1 Case decision classes

### Auto-pass eligible

A case may be auto-processed only if all conditions are true:

1. All mandatory documents for the workflow are present.
2. All mandatory fields are extracted at or above high-confidence threshold.
3. No hard-fail rule is triggered.
4. No critical or high-risk exception code is present.
5. All exact-match fields pass cross-document comparison.
6. All tolerance-based fields are within auto-pass limits.
7. Workflow policy allows STP for that product and risk tier.

### Manual review required

A case must route to manual review if any of the following is true:

1. Any mandatory field confidence falls below auto-pass threshold.
2. Any soft inconsistency exists across name, address, employer, or income.
3. Any document freshness check is ambiguous.
4. Statement parsing is incomplete but still partly usable.
5. Applicant is in a workflow where first-release policy mandates human approval.

### Hard fail / reject / resubmit

A case must not proceed without corrected documentation if any of the following is true:

1. Required document missing.
2. Primary identity document expired or invalid.
3. Consent form missing when required.
4. Date of birth mismatch across identity and application.
5. Material name mismatch with no permitted alias logic.
6. Income evidence materially fails declared amount beyond threshold and no acceptable explanation exists.
7. Document suspected to be altered.

## 7.2 Recommended thresholds

### Extraction confidence thresholds

| Condition | Threshold | Action |
|---|---:|---|
| Mandatory identity field confidence | >= 0.95 | Eligible for auto-pass |
| Mandatory address or income field confidence | >= 0.92 | Eligible for auto-pass |
| Confidence between 0.80 and threshold | Review | Manual review |
| Confidence < 0.80 on mandatory field | High severity | Manual review or resubmission based on readability |

### Cross-document thresholds

| Field comparison | Auto-pass | Manual review | Hard fail |
|---|---|---|---|
| Date of birth | Exact match | None | Any mismatch |
| Document number recheck | Exact match | One unclear character | Clear mismatch |
| Full name | Exact or approved normalized near-match | Token differences explainable by initials/middle names/marital changes | Material mismatch |
| Address | Core address exact or near-exact after normalization | Unit/postal/street abbreviation differences | Clearly different residence |
| Income variance declared vs verified | <= 10% | > 10% and <= 20% | > 20% |

### Freshness thresholds

| Document | Auto-pass | Manual review | Hard fail |
|---|---|---|---|
| Utility bill | <= 90 days | Date unclear or slight staleness if policy override exists | Older than max policy without override |
| Payslip | <= 60 days | 61 to 90 days if workflow allows | Older than policy maximum |
| Employment letter | <= 90 days | Older but supported by strong secondary proof | Too old and unsupported |
| Bank statement | Full required period present | Small gap explainable | Material missing period |

## 8. Workflow-Specific Rules

## 8.1 KYC onboarding

### Required minimum pack

1. One primary identity document
2. One proof-of-address document if address verification required by product/jurisdiction

### Auto-pass allowed only if

1. Identity document valid and not expired
2. Name and DOB pass exact/near-exact rules
3. Address proof fresh and matches application
4. No fraud or sanctions flags
5. Policy explicitly permits STP for low-risk segment

### Mandatory human review

1. Any first-release KYC decision if policy says so
2. Any mismatch between ID and address proof
3. Any document quality concern

## 8.2 Income verification

### Required minimum pack

1. Recent payslip or salary certificate
2. Bank statement if the product requires income corroboration

### Auto-pass allowed only if

1. Employer and employee names align
2. Pay amount is clear
3. Salary frequency can be normalized
4. Bank statement shows supporting salary behavior when required
5. Declared income variance is within threshold

### Mandatory human review

1. Variable income or commission-based income
2. Missing clear salary credit despite supplied statement
3. Employer mismatch or payroll processor ambiguity

## 8.3 Loan document intake

### Required minimum pack

1. Current loan application form
2. Required consent forms
3. Identity document
4. Income support documents where applicable

### Auto-pass allowed only if

1. Application is complete
2. Required signatures/consents present
3. Requested amount present and parsable
4. Applicant identity and income checks pass

### Mandatory human review

1. Corrected application values
2. Any handwritten amendments
3. High-value loan thresholds

## 9. Assumption Review for Business Realism

## 9.1 Assumptions that are realistic

1. Queue-based review is operationally correct.
2. Append-only audit is non-negotiable.
3. Revalidation after correction is necessary.
4. Straight-through processing should start only with narrow low-risk use cases.

## 9.2 Assumptions that would be operationally weak if left unchallenged

1. "If OCR is accurate, the document is usable."
   - Not true. Validity, freshness, and consistency matter as much as extraction.
2. "Any proof of address is equivalent."
   - Not true. Issuer quality, freshness, and service-vs-mailing address matter.
3. "Payslip alone proves income."
   - Often not enough for lending; statement corroboration may still be required.
4. "Name near-match always means pass."
   - Not true. Some near-matches are acceptable; DOB mismatches are not.
5. "Auto-reject is safe if a rule fails."
   - Not true. Many failures should lead to resubmission or manual review, not direct rejection.
6. "Invoices can be treated like retail documents."
   - Not true. Commercial documents usually need supporting pack logic.

## 9.3 Engineering guidance

1. Every rule should emit:
   - rule_id
   - severity
   - result
   - reason_code
   - evidence_refs
2. Separate "field missing in source document" from "field not extracted confidently."
3. Preserve original extracted value and reviewer-corrected value.
4. Make freshness windows configurable by workflow and jurisdiction.
5. Support document-type-specific validation plugins rather than one shared generic validator.

## 10. Minimum Implementable Rule Set

If engineering needs the first strict version, implement these first:

1. Identity document mandatory fields and expiry validation
2. Address proof freshness and name/address comparison
3. Payslip employer and pay-amount validation
4. Bank statement period coverage and account-holder-name extraction
5. Loan application completeness and consent signature checks
6. Cross-document checks for name, DOB, address, employer, and income variance
7. Routing logic for auto-pass, review, escalate, and hard fail

This is the minimum rule set that will produce operationally useful outcomes instead of technically correct but unusable extraction output.

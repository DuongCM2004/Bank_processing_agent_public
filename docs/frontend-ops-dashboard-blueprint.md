# Frontend Ops Dashboard Blueprint for Ops Agent

## Role

Frontend Engineer / Ops Dashboard Engineer for a banking-grade Document Processing Agent.

## Objective

Design and build the user-facing operations dashboard and review interfaces for document upload, case tracking, evidence review, correction, escalation, and audit visibility.

## Assumptions

1. The frontend is an internal operations workstation built with React / Next.js.
2. Core users are operations reviewers, compliance analysts, fraud analysts, branch support teams, back-office staff, and supervisors.
3. Backend APIs and workflow states follow the current FastAPI foundation and the backend blueprint.
4. The UI must make uncertainty, evidence, and workflow status explicit at all times.
5. The UI must never imply that a case is compliant or approved when critical checks remain pending.

## Deliverables

- UI architecture
- Screen flow
- Components
- Review UX
- Correction UX
- Escalation UX
- Audit UX

## Dependencies

1. [ops-agent-prd.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ops-agent-prd.md)
2. [solution-architecture-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\solution-architecture-blueprint.md)
3. [backend-engineering-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\backend-engineering-blueprint.md)
4. [compliance-risk-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\compliance-risk-controls.md)
5. [ai-architecture.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ai-architecture.md)

## Risks

1. the UI becomes an admin panel instead of a high-speed review workstation
2. evidence and extracted values are separated too far apart, slowing review
3. role differences are hidden, causing unsafe actions to appear available
4. too much detail is shown at once, causing cognitive overload
5. uncertainty and pending compliance checks are visually weak

## MVP vs Scale notes

### MVP

1. prioritize queue work, case detail, evidence review, correction, escalation, and audit visibility
2. keep navigation shallow
3. support only the workflows and document types in MVP
4. build a compact, analyst-first workstation rather than a generalized reporting suite

### Scale

1. add supervisor analytics, richer case search, saved views, and more workflow-specific panels
2. add cross-case entity views and broader exception analytics
3. expand layout support for more document types and specialist workbenches

## 1. UI Architecture

## 1.1 Frontend architecture

Use a Next.js application with route groups organized by operational domain:

```text
/app
  /login
  /dashboard
  /intake
  /cases
    /[caseId]
  /review-tasks
    /[taskId]
  /queues
  /audit
  /admin (restricted)
```

## 1.2 State model

Use three UI state layers:

1. server state:
   - case details
   - review tasks
   - audit events
   - extracted fields
   - compliance control statuses
2. local interaction state:
   - selected document
   - selected page
   - selected field
   - comparison mode
   - unsaved corrections
3. access-control state:
   - role permissions
   - visible actions
   - hidden sensitive panels

## 1.3 Layout strategy

The workstation should follow a three-panel review layout for detail pages:

1. left panel: case/document navigation and status summary
2. center panel: document viewer with evidence highlights
3. right panel: extraction, validation, compliance, and actions

This reduces context switching and makes evidence comparison fast.

## 2. Screen Flow

## 2.1 Primary user journeys

### Branch support

1. login
2. upload documents through intake form
3. confirm case creation
4. view basic status and missing-document requests

### Operations reviewer

1. login
2. land on queue dashboard
3. filter tasks by queue, status, priority, and reason code
4. open task
5. compare evidence and extracted fields
6. correct fields or escalate
7. revalidate
8. close or pass to specialist

### Compliance / fraud analyst

1. open specialist queue
2. review escalated cases
3. inspect compliance control panel and evidence
4. record disposition
5. approve, reject, or keep escalated

### Back-office user

1. open closed/approved cases
2. download approved structured package
3. confirm downstream handoff

## 2.2 Screen map

| Screen | Purpose | Primary users |
|---|---|---|
| Login | secure access | all |
| Dashboard home | queue and workload entry point | ops, compliance, fraud, supervisors |
| Intake upload | case creation and document submission | branch, ops |
| Queue list | work queue and triage | ops, compliance, fraud |
| Case detail | full evidence and workflow view | ops, compliance, fraud, back office |
| Review task detail | focused review workspace | ops, compliance, fraud |
| Audit explorer | event reconstruction | compliance, supervisors, audit-facing users |
| Admin / config | limited operational admin tools | supervisors, admins |

## 3. Component Map

## 3.1 Global components

1. `AppShell`
2. `TopNav`
3. `RoleAwareSidebar`
4. `PermissionGuard`
5. `GlobalSearchBar`
6. `TraceBanner`
7. `StatusBadge`
8. `PriorityBadge`
9. `EmptyState`
10. `ErrorPanel`

## 3.2 Dashboard components

1. `QueueSummaryCards`
2. `MyTasksTable`
3. `SlaAlertBanner`
4. `RecentEscalationsPanel`
5. `CompliancePendingPanel`
6. `SavedFiltersBar`

## 3.3 Case detail components

1. `CaseHeader`
2. `CaseStatusRail`
3. `DocumentTabs`
4. `DocumentViewer`
5. `EvidenceOverlay`
6. `FieldReviewPanel`
7. `ValidationPanel`
8. `ComplianceControlPanel`
9. `ActionPanel`
10. `AuditTimelinePreview`

## 3.4 Correction and escalation components

1. `FieldCorrectionForm`
2. `EvidencePicker`
3. `ReasonCodeSelect`
4. `EscalationModal`
5. `RevalidationBanner`
6. `DecisionConfirmDialog`

## 3.5 Audit components

1. `AuditTimeline`
2. `AuditEventDrawer`
3. `VersionTracePanel`
4. `ActorFilter`
5. `ExportAuditButton`

## 4. Upload and Intake UX

## 4.1 Intake goals

The intake flow should:

1. minimize required input for branch and ops staff
2. prevent bad submissions early
3. make required document packs visible
4. show upload success and failure explicitly

## 4.2 Intake screen structure

### Section 1: case metadata

1. workflow type
2. priority
3. customer reference
4. source channel

### Section 2: required documents checklist

1. checklist updates based on workflow type
2. required vs optional distinction
3. freshness hints and document examples

### Section 3: document upload zone

1. drag-and-drop upload
2. multi-file upload
3. file validation chips:
   - accepted
   - duplicate
   - unsupported type
   - password-protected

### Section 4: submission confirmation

1. created case ID
2. queue assignment
3. initial status
4. document count

## 4.3 Intake UX rules

1. reject unsupported file types inline before submit where possible
2. show file-level errors next to the file, not in a generic toast only
3. do not expose review-only controls to branch users
4. if upload partially succeeds, show which documents were accepted and which were not

## 5. Case List and Case Detail UX

## 5.1 Queue / case list UX

The queue screen should optimize for fast triage.

### Table columns

1. case ID
2. workflow type
3. current status
4. compliance status
5. priority
6. assigned queue
7. reason codes
8. document count
9. updated time

### Filters

1. queue
2. task status
3. workflow type
4. priority
5. reason code
6. pending compliance checks
7. escalated only

### Row design

1. use compact status badges
2. show high-severity exceptions inline
3. show pending compliance checks as a separate visual token

## 5.2 Case detail UX

The case detail screen is the operational center of the product.

### Header block

1. case ID
2. workflow type
3. status
4. compliance status
5. queue
6. assignee
7. priority

### Left rail

1. document list
2. checklist completion
3. quick jumps:
   - extraction
   - validation
   - compliance
   - audit

### Center workspace

1. selected document viewer
2. page thumbnails
3. zoom and pan
4. evidence highlights

### Right rail

1. extracted fields grouped by category
2. validation results grouped by severity
3. compliance control statuses
4. action buttons

## 6. Evidence and Extraction Review UX

## 6.1 Core review pattern

Every extracted field row should show:

1. field name
2. extracted value
3. normalized value
4. confidence label and score
5. method tag:
   - rule
   - ML
   - LLM fallback
   - reviewer corrected
6. one-click "show evidence"

## 6.2 Evidence interaction

When the reviewer clicks a field:

1. highlight the matching page and bounding box in the viewer
2. scroll the viewer to the matching location
3. show the OCR text span and artifact source
4. show any conflicting candidates

## 6.3 Visual uncertainty model

Use explicit, restrained visual cues:

1. `high_confidence`: neutral/positive tag
2. `medium_confidence`: amber tag
3. `low_confidence`: red/attention tag
4. `not_confident`: outlined warning state

Do not hide low-confidence fields in collapsed sections. They should be visible near the top of the field list.

## 6.4 Comparison mode

Enable a compare mode for critical cases:

1. extracted vs normalized values side by side
2. document A vs document B for cross-document mismatches
3. original extracted value vs reviewer correction

## 7. Manual Correction UX

## 7.1 Correction interaction model

Correction should be inline and low-friction:

1. click field
2. open inline edit state
3. show current value, normalized value, and evidence refs
4. enter corrected value
5. require reason code
6. require evidence link for critical fields
7. save draft or submit correction

## 7.2 Correction rules in UI

1. critical identity, DOB, address, and income fields require evidence before save
2. corrected values must visually replace the active value but preserve original extracted value below
3. every correction should display:
   - corrected by
   - timestamp
   - reason code

## 7.3 Revalidation UX

After correction:

1. show `Ready for revalidation` state
2. disable final close actions until revalidation completes where policy requires it
3. show revalidation result summary inline:
   - passed
   - still review required
   - escalated

## 8. Escalation / Review UX

## 8.1 Escalation flow

The escalation action should open a structured modal with:

1. escalation target:
   - ops review
   - compliance review
   - fraud review
   - manual resubmission
2. required reason code
3. optional comment
4. evidence selection summary

## 8.2 Specialist review workspace

Compliance and fraud users should see:

1. specialist-only queue
2. high-severity reasons pinned at top
3. compliance control panel expanded by default
4. audit timeline expanded by default
5. restricted action set based on permissions

## 8.3 Exception handling UX

For exceptions:

1. group by severity:
   - critical blockers
   - high severity
   - informational warnings
2. show recommended next action
3. show whether human action is mandatory

## 9. Audit Trail UX

## 9.1 Audit principles

Audit visibility must allow a reviewer, supervisor, or auditor-facing user to reconstruct:

1. what changed
2. when it changed
3. who changed it
4. what evidence and versions were used

## 9.2 Audit timeline design

Each event row should show:

1. timestamp
2. actor
3. action
4. resource type
5. short summary
6. expandable payload

## 9.3 Audit details drawer

Expanded details should include:

1. old value / new value if relevant
2. trace ID
3. model/prompt/rule versions
4. linked evidence refs
5. linked review action or workflow event

## 9.4 Audit usability rules

1. keep audit timeline read-only
2. allow filtering by actor, action type, and time range
3. provide export only to authorized roles

## 10. Role-Based UI Behavior

## 10.1 Role matrix

| Role | Upload | Review fields | Correct fields | Escalate | Approve/reject | View audit | View restricted fraud/compliance details |
|---|---|---|---|---|---|---|---|
| Branch support | yes | limited | no | no | no | limited | no |
| Operations reviewer | yes | yes | yes | yes | limited to delegated workflows | yes | no |
| Compliance analyst | yes | yes | yes | yes | yes | yes | compliance only |
| Fraud analyst | no | yes | limited | yes | yes for fraud-reviewed cases | yes | fraud only |
| Back office | no | final package only | no | no | no | limited | no |
| Supervisor | yes | yes | limited | yes | limited by policy | yes | role-scoped |

## 10.2 UI enforcement rules

1. hide actions the user can never take
2. disable actions the user can take only under current state constraints
3. show explanatory tooltip when an action is unavailable because of workflow or compliance state

Examples:

1. close button disabled when critical compliance checks are pending
2. approve button hidden for branch users
3. restricted compliance notes hidden outside compliance roles

## 11. Recommended Implementation Sequence

1. app shell, auth integration, and role-aware navigation
2. queue list and case list
3. case detail screen with document viewer
4. field review panel and evidence overlay
5. correction workflow
6. escalation modal and specialist queue variants
7. audit timeline and event details
8. polish, keyboard shortcuts, saved filters, and performance tuning

## 12. Recommended Frontend Stance

The Ops Agent frontend should behave like a focused review workstation, not a general-purpose admin console.

That means:

1. queue first,
2. evidence always near the extracted value,
3. uncertainty impossible to miss,
4. corrections fast but controlled,
5. audit and compliance status visible without clutter.

That is the right UX model for banking operations work.

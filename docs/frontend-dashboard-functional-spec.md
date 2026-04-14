# Frontend Dashboard Functional Specification for Ops Agent

## Role

Senior Frontend Product Designer and Ops Dashboard Designer for a banking-grade Document Processing Agent.

## Objective

Define the screens, flows, components, information hierarchy, and role-based interactions needed for operations, compliance, and review users in a form that frontend engineers can implement directly.

## Assumptions

1. The frontend is an internal React / Next.js workstation.
2. The backend APIs follow the current case-centric contract defined in [api-specification.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\api-specification.md).
3. The UI must make source evidence, uncertainty, workflow status, and allowed actions obvious at all times.
4. Human review is a first-class part of the workflow, not an exception path.
5. MVP scope remains limited to retail KYC onboarding, income verification, bank statement analysis, and loan document intake.

## Deliverables

- User roles
- Primary user journeys
- Navigation structure
- Screen inventory
- Case list page spec
- Case detail page spec
- Document viewer spec
- Extracted field review panel spec
- Validation and issue panel spec
- Manual correction flow
- Escalation flow
- Audit history view
- Empty / error / loading states
- MVP dashboard scope
- Scale-stage UX improvements

## Dependencies

1. [ops-agent-prd.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ops-agent-prd.md)
2. [frontend-ops-dashboard-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\frontend-ops-dashboard-blueprint.md)
3. [api-specification.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\api-specification.md)
4. [backend-service-decomposition.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\backend-service-decomposition.md)
5. [compliance-risk-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\compliance-risk-controls.md)

## Risks

1. The UI turns into a generic dashboard instead of a high-speed review workstation.
2. Reviewers must jump between too many screens to compare evidence and extracted data.
3. Low-confidence or pending-compliance states are visually weak and create unsafe operator assumptions.
4. Role-based action rules are enforced in backend only and not reflected clearly in the UI.
5. Too much metadata is shown without hierarchy, slowing reviewers instead of helping them.

## MVP vs Scale Notes

### MVP

1. Prioritize queue-based work, case review, evidence comparison, correction, escalation, and audit visibility.
2. Keep navigation shallow and role-aware.
3. Prefer one primary review workstation over many specialized pages.

### Scale

1. Add supervisor analytics, saved views, advanced filtering, and broader exception drill-down.
2. Add specialist workbenches for compliance, fraud, and quality assurance.
3. Add richer search, notifications, collaboration features, and cross-case relationship views.

## 1. User Roles

| Role | Primary goal | Key actions | Restricted actions |
|---|---|---|---|
| `branch_support` | create case and upload documents | create case, upload files, view basic status | cannot correct extracted fields, approve, reject, escalate to restricted queues |
| `ops_reviewer` | process standard review queue efficiently | claim task, inspect evidence, correct fields, revalidate, escalate | cannot clear compliance-sensitive cases outside delegated authority |
| `compliance_analyst` | resolve compliance-sensitive cases | view full compliance panels, specialist review, approve or reject within policy | cannot bypass audit or hide pending checks |
| `fraud_analyst` | investigate suspicious cases | inspect anomaly evidence, review escalations, block unsafe progression | cannot silently downgrade fraud flags |
| `back_office` | consume final case result | view final package, confirm handoff | cannot change extraction or review data |
| `supervisor` | manage queues and throughput | view queues, reassign or reprioritize where allowed, inspect backlog | cannot delete history or bypass policy-gated decisions |
| `platform_admin` | operational setup and support | manage configuration screens in restricted areas | should not use reviewer actions as normal workflow path |

## 2. Primary User Journeys

### 2.1 Branch or intake journey

1. User opens `Intake`.
2. User selects workflow type and enters customer reference.
3. User uploads one or more documents.
4. System validates upload metadata and shows per-file acceptance or rejection.
5. User submits case and lands on case confirmation view.
6. User can open the created case and see initial status, queue, and missing-document hints.

### 2.2 Operations reviewer journey

1. User lands on queue-focused home.
2. User filters to their assigned queue or high-priority work.
3. User opens a review task from the case list or task list.
4. User sees case summary, document viewer, extracted fields, validation findings, and action rail on one screen.
5. User corrects fields, revalidates, escalates, or closes if allowed.
6. System confirms action, updates state, and preserves audit trail.

### 2.3 Compliance or fraud analyst journey

1. User opens specialist queue.
2. User selects escalated case.
3. User inspects issue panel, evidence, control statuses, and prior reviewer actions.
4. User records specialist disposition, escalates further, or closes within role authority.

### 2.4 Back-office journey

1. User opens completed case list.
2. User filters to approved or closed cases.
3. User opens case detail in read-only mode.
4. User downloads or forwards final structured output package.

## 3. Navigation Structure

### 3.1 Primary navigation

Recommended primary nav:

1. `Home`
2. `Intake`
3. `Queues`
4. `Cases`
5. `Audit`
6. `Admin` (restricted)

### 3.2 Route structure

```text
/login
/home
/intake
/queues
/cases
/cases/[caseId]
/review-tasks/[taskId]
/audit
/audit/[caseId]
/admin
```

### 3.3 Navigation rules

1. `Home` and `Queues` are default landing pages for reviewers and analysts.
2. `Intake` is emphasized for branch and intake users.
3. `Case detail` is the primary work surface and must be reachable from both queues and search.
4. Users should never need to open a separate page just to compare extraction to evidence.

## 4. Screen Inventory

| Screen | Purpose | Primary roles | MVP |
|---|---|---|---|
| Login | authenticate user | all | yes |
| Home / Queue home | show workload entry points and personal queue summary | ops, compliance, fraud, supervisor | yes |
| Intake | create case and upload documents | branch, ops | yes |
| Queue list | triage work items | ops, compliance, fraud, supervisor | yes |
| Case list | search and browse cases | all operational roles | yes |
| Case detail / review workstation | inspect evidence, fields, issues, actions | ops, compliance, fraud, back office | yes |
| Review-task direct entry | deep link into active review task | ops, compliance, fraud | yes |
| Audit explorer | inspect audit timeline and event details | compliance, supervisor, admin | yes |
| Supervisor dashboard | queue analytics and SLA views | supervisor | future |
| Specialist workbench | role-specific advanced views | compliance, fraud | future |

## 5. Case List Page Specification

### 5.1 Page purpose

Provide fast triage and routing into case detail or task detail.

### 5.2 Data sources

Primary API dependencies:

1. `GET /v1/review-tasks`
2. `GET /v1/cases` when available in scale phase
3. `GET /v1/cases/{case_id}` for refresh-on-demand or row expansion

### 5.3 Page layout

1. top filter bar
2. summary chips row
3. table or dense list of cases / tasks
4. right-side optional preview drawer for selected row

### 5.4 Required filters

MVP filters:

1. status
2. assigned queue
3. priority
4. reason code

Future filters:

1. assigned reviewer
2. workflow type
3. age bucket
4. customer reference

### 5.5 Table columns

Required columns in MVP:

1. case id
2. workflow type
3. current status
4. assigned queue
5. priority
6. reason codes summary
7. created time
8. updated time
9. assignee

### 5.6 Row interactions

1. clicking row opens case detail
2. clicking task link opens review-task deep link
3. status and priority are shown as persistent badges
4. unresolved uncertainty must be visible in-row via warning icon or badge

### 5.7 Efficiency rules

1. filter changes must not require full page reload
2. keyboard navigation should support moving across list rows
3. the table must support dense view for power users
4. case id and customer reference should be copyable

## 6. Case Detail Page Specification

### 6.1 Page purpose

Serve as the main review workstation for evidence inspection, correction, escalation, and closure.

### 6.2 Page layout

Three-column layout on desktop:

1. left rail
   case summary, workflow state, task state, document list, quick navigation
2. center workspace
   document viewer with overlays
3. right action rail
   extracted fields, validation issues, compliance status, action controls

Mobile or narrow fallback:

1. stacked tabbed layout
2. viewer remains primary tab
3. actions and issues accessible without losing current document selection

### 6.3 Header section

Required elements:

1. case id
2. workflow type
3. priority badge
4. current case status
5. compliance status badge
6. current assignee
7. key actions allowed for current role

### 6.4 Left rail

Required modules:

1. case summary card
2. document list with per-document status
3. review task card
4. issue count summary
5. audit shortcut

### 6.5 Right rail

Required modules:

1. extracted field review panel
2. validation and issues panel
3. compliance panel
4. actions panel

### 6.6 Core interaction rule

The page must support reviewing one document while seeing all case-level issues without losing context.

## 7. Document Viewer Specification

### 7.1 Purpose

Allow reviewers to verify extracted data directly against source evidence quickly.

### 7.2 Required capabilities

1. page thumbnails
2. page zoom and pan
3. next / previous page
4. highlight bounding boxes from evidence refs
5. OCR text overlay toggle
6. fit-to-width and fit-to-page controls

### 7.3 Evidence interaction behavior

1. clicking a field in the field review panel highlights the source evidence in the viewer
2. clicking an issue in the issue panel highlights related evidence when available
3. if multiple evidence refs exist, viewer cycles or lists them
4. missing evidence is shown as an explicit warning, not as a silent empty state

### 7.4 Visual hierarchy rules

1. source image remains primary
2. evidence highlights are visible but not visually noisy
3. low-confidence evidence uses a different visual treatment than confirmed evidence
4. pending or missing pages are called out visibly in the page rail

## 8. Extracted Field Review Panel Specification

### 8.1 Purpose

Allow reviewers to inspect, compare, and correct extracted fields with minimal effort.

### 8.2 Grouping

Fields grouped by section:

1. identity
2. address
3. income
4. statement metadata
5. loan packet metadata

### 8.3 Required row content

Each field row shows:

1. field label
2. extracted value
3. normalized value if different
4. confidence badge
5. required / optional marker
6. reason code if missing or conflicted
7. evidence link
8. correction action if allowed

### 8.4 Comparison behavior

1. if normalized value differs materially, show both original and normalized values
2. if a reviewer corrected the field, show machine value and reviewer-confirmed value distinctly
3. unresolved conflicts display candidate values instead of one forced value

### 8.5 Uncertainty rules

1. low-confidence rows are visually promoted
2. missing required fields pin to the top of the section
3. conflicts must show explicit reason codes and evidence gaps

## 9. Validation and Issue Panel Specification

### 9.1 Purpose

Help reviewers understand what is blocking progress and why.

### 9.2 Required sections

1. blocking issues
2. non-blocking warnings
3. compliance-sensitive issues
4. pending checks

### 9.3 Issue item content

Each issue item shows:

1. issue title or rule id
2. severity
3. reason code
4. impacted field or document
5. linked evidence if available
6. current disposition state

### 9.4 Sorting

Sort issues in this order:

1. critical blocking issues
2. pending critical checks
3. high severity warnings
4. informational warnings

### 9.5 Interaction rules

1. selecting an issue highlights related evidence and field rows
2. resolved issues remain visible in history but visually differentiated
3. compliance-pending must never appear visually similar to pass

## 10. Manual Correction Flow

### 10.1 Entry points

1. inline correction from field row
2. correction action from issue panel
3. correction shortcut from action rail

### 10.2 Flow steps

1. reviewer selects field
2. correction drawer or modal opens
3. reviewer enters corrected value
4. reviewer selects mandatory reason code
5. reviewer attaches or confirms evidence reference
6. reviewer submits correction
7. UI shows pending revalidation state
8. reviewer triggers revalidation or system prompts for it

### 10.3 UX rules

1. original machine value remains visible
2. correction reason is mandatory for material fields
3. correction is disabled for unauthorized roles
4. unsaved edits show explicit dirty state
5. after submit, the corrected row is marked as reviewer-confirmed

## 11. Escalation Flow

### 11.1 Entry points

1. action rail escalation button
2. issue panel escalation CTA for compliance or fraud-sensitive issues

### 11.2 Flow steps

1. reviewer opens escalation modal
2. reviewer selects target queue
3. reviewer selects reason code
4. reviewer adds optional comment
5. reviewer submits escalation
6. case status updates to `escalated`
7. queue ownership and audit history update visibly

### 11.3 UX rules

1. escalation targets are role-aware
2. invalid or unauthorized targets are not shown
3. escalated state is persistent and prominent in header and left rail
4. prior reviewer notes remain visible to specialist users

## 12. Audit History View

### 12.1 Purpose

Allow users to reconstruct case progression and reviewer actions without leaving the workstation.

### 12.2 Placement

1. compact preview in case detail right or left rail
2. full-screen or full-tab audit explorer from case detail

### 12.3 Timeline content

Each timeline event shows:

1. timestamp
2. actor type and actor id
3. action
4. affected resource
5. reason code
6. details preview

### 12.4 Detail drawer

On event click, show:

1. full structured details
2. version references
3. linked resources
4. related evidence or artifact refs where applicable

### 12.5 UX rules

1. audit history is read-only
2. timeline is chronological
3. missing events or retrieval errors are explicit
4. export controls are role-gated

## 13. Empty, Error, and Loading States

### 13.1 Empty states

1. queue empty
   show "no tasks in current filter" with filter reset shortcut
2. no documents on case
   show missing-document guidance and intake next step
3. no audit events available
   show retrieval guidance and trace id if available

### 13.2 Error states

1. API fetch failure
   show retry CTA and trace id
2. permission denied
   show restricted-access message without leaking hidden content
3. artifact retrieval failure
   keep case usable and show evidence-unavailable warning

### 13.3 Loading states

1. list page
   skeleton rows
2. case detail
   skeleton header plus panel placeholders
3. revalidation in progress
   persistent banner with non-blocking progress state

### 13.4 State design rule

No empty, error, or loading state should look like successful completion.

## 14. MVP Dashboard Scope

### 14.1 Included in MVP

1. login
2. intake screen
3. queue and case list
4. case detail review workstation
5. document viewer with evidence highlights
6. extracted field panel
7. validation and compliance issue panel
8. correction flow
9. escalation flow
10. audit timeline view

### 14.2 Deferred from MVP

1. saved views
2. advanced global search
3. supervisor analytics dashboard
4. threaded collaboration comments
5. notification center
6. cross-case relationship views

## 15. Scale-Stage UX Improvements

### 15.1 Operations efficiency upgrades

1. saved filters and saved queue views
2. bulk triage for low-risk operational tasks
3. keyboard-first review shortcuts
4. richer queue aging and SLA indicators

### 15.2 Specialist UX upgrades

1. compliance-only workbench
2. fraud-only anomaly and duplicate view
3. cross-case entity and repeat-document drilldown

### 15.3 Search and analytics upgrades

1. global case and document search
2. reviewer performance and override analytics for supervisors
3. issue trend exploration by workflow and reason code

## 16. Recommended Frontend Stance

The frontend should behave as:

1. a focused review workstation, not a generic admin dashboard,
2. evidence-first by default,
3. explicit about uncertainty and pending controls,
4. role-aware in visible actions and panel visibility,
5. optimized to reduce reviewer clicks and context switching.

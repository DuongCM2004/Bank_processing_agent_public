# Execution Delivery Plan for Ops Agent

## Current Documents Module Baseline

Delivery for the Documents extraction module must follow [production-llm-document-extraction-backend-spec.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\production-llm-document-extraction-backend-spec.md). Workstreams should sequence upload/storage, async extraction workers, Pillow preprocessing, LangGraph orchestration, GPT-4o Vision adapter, strict schema validation, one retry, normalization, manual review, approved-only persistence, audit trail, and UUID search. Do not schedule dataset preparation, training, benchmarking, or model-evaluation work for the current Documents extraction release.

## Role

Project Manager / Delivery Manager for a banking-grade Document Processing Agent.

## Objective

Turn the existing product, architecture, AI, backend, frontend, security, QA, and operations specifications into a build-ready delivery roadmap for MVP, hardening, and scale transition.

## Assumptions

1. The initial delivery target is an MVP that supports a narrow, controlled banking operations workflow with mandatory human review for KYC approval and all high-risk cases.
2. The existing repo and specification set are the baseline source of truth for scope, architecture, controls, and quality gates.
3. Delivery must keep architecture coherent, but MVP must avoid unnecessary service fragmentation or overbuilt platform work.
4. Compliance, auditability, and security controls are first-release requirements, not post-MVP cleanup.
5. All workstreams must produce artifacts that are directly consumable by downstream teams.

## Deliverables

- Workstreams
- Task breakdown by team
- Milestones
- Dependency tracking
- Critical path
- Suggested sprint plan
- MVP build sequence
- Testing and hardening phase
- Pre-production readiness checklist
- Go-live readiness checklist
- Risks and mitigations
- Scale-stage transition plan

## Dependencies

1. [ops-agent-prd.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ops-agent-prd.md)
2. [solution-architecture-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\solution-architecture-blueprint.md)
3. [ai-architecture.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ai-architecture.md)
4. [prompt-system.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\prompt-system.md)
5. [banking-document-rules.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\banking-document-rules.md)
6. [compliance-risk-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\compliance-risk-controls.md)
7. [backend-service-decomposition.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\backend-service-decomposition.md)
8. [api-specification.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\api-specification.md)
9. [database-persistence-schema.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\database-persistence-schema.md)
10. [shared-data-contracts.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\shared-data-contracts.md)
11. [frontend-dashboard-functional-spec.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\frontend-dashboard-functional-spec.md)
12. [security-architecture-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\security-architecture-controls.md)
13. [qa-engineering-test-strategy.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\qa-engineering-test-strategy.md)
14. [devops-mlops-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\devops-mlops-blueprint.md)

## Risks

1. Teams start implementation before shared contracts, schemas, and ownership boundaries are frozen.
2. AI and workflow workstreams move faster than compliance, audit, and QA readiness, creating rework.
3. MVP gets bloated by scale-stage concerns such as multi-region, advanced drift automation, or broad channel support.
4. External dependency readiness, especially sanctions and screening adapters, slips late and blocks pilot readiness.
5. Release readiness is treated as an operations step rather than a full cross-functional exit gate.

## MVP vs Scale Notes

### MVP

1. Build one narrow end-to-end path completely:
   case intake, document registration, OCR, classification, extraction, validation, review task creation, manual correction, revalidation, decision, audit trail, and ops dashboard.
2. Keep workflow scope focused on in-scope MVP document types and controlled automation boundaries.
3. Ship with conservative routing and explicit review queues rather than chasing high straight-through automation too early.

### Scale

1. Expand channels, document coverage, model sophistication, and automation scope only after stable operational evidence.
2. Add stronger service isolation, canary model operations, broader reporting, and regional resilience after MVP and beta controls are proven.

## 1. Workstreams

| Workstream | Primary Owner | Purpose | Output |
| --- | --- | --- | --- |
| Product and Delivery | Product Manager + Delivery Manager | scope, acceptance, sequencing, decision log | prioritized backlog and release plan |
| Banking Rules and Compliance | Domain Expert + Compliance Lead | business rules, control boundaries, review policy | implementable rules and control pack |
| Solution and Platform Architecture | Solution Architect | system boundaries and delivery alignment | frozen MVP technical blueprint |
| Backend and Workflow | Backend Lead | APIs, orchestration, persistence, case state | runnable backend services |
| AI and ML | AI Architect + ML Lead | OCR, classification, extraction, confidence, fallbacks | deployed AI pipeline |
| Data and Contracts | Data Engineer | schemas, lineage, datasets, evidence traceability | shared contracts and persistence models |
| Frontend Ops Workstation | Frontend Lead | review UI, evidence viewer, correction and escalation UX | reviewer-facing dashboard |
| Security and Identity | Security Lead | auth, access, encryption, secure handling, audit protection | enforced security baseline |
| DevOps and MLOps | Platform Lead | environments, CI/CD, observability, rollout and rollback | operable staging and production path |
| QA and UAT | QA Lead | test automation, test data, release gates, UAT | validated MVP release candidate |

## 2. Task Breakdown by Team

### 2.1 Product and Delivery

#### Design tasks

1. Freeze MVP scope, personas, use cases, and acceptance criteria.
2. Finalize automation boundaries and mandatory human-review policies.
3. Convert PRD features into epics and sprint-ready stories with owners.

#### Build tasks

1. Maintain delivery board, milestone tracking, and dependency log.
2. Run weekly scope, risk, and blocker review with leads.

#### Test tasks

1. Coordinate UAT plan with operations, compliance, and product stakeholders.
2. Validate that delivered scope matches PRD acceptance criteria.

#### Release tasks

1. Own go/no-go deck and unresolved-risk register.
2. Confirm operational readiness sign-offs are complete before pilot release.

### 2.2 Banking Rules and Compliance

#### Design tasks

1. Freeze MVP document taxonomy, required fields, thresholds, and exception codes.
2. Freeze compliance control matrix and human-approval policy.

#### Build tasks

1. Support rule implementation, reason-code definitions, and review queue logic.
2. Approve workflow treatment for pending, failed, escalated, and non-compliant cases.

#### Test tasks

1. Review rule coverage and compliance test cases.
2. Validate decision outputs for realistic banking scenarios.

#### Release tasks

1. Sign off on regulated workflow completeness and escalation handling.

### 2.3 Solution and Platform Architecture

#### Design tasks

1. Freeze service boundaries, integration patterns, and artifact ownership.
2. Freeze MVP non-functional requirements and dependency model.

#### Build tasks

1. Resolve cross-team interface questions and architecture deviations.
2. Review implementation proposals for contract and boundary violations.

#### Test tasks

1. Review integration and deployment readiness against architecture blueprint.

#### Release tasks

1. Approve any MVP scope cuts or compensating controls required for launch.

### 2.4 Backend and Workflow

#### Design tasks

1. Finalize API contracts, case state machine, retry model, and event schemas.
2. Finalize DB migrations and persistence boundaries.

#### Build tasks

1. Implement case intake, document registration, results retrieval, review APIs, and audit retrieval.
2. Implement Temporal workflows, queue integration, idempotency, and explicit workflow states.
3. Implement persistence models, migrations, audit writes, and error handling.

#### Test tasks

1. Build unit, contract, and integration tests for workflow-safe transitions.
2. Validate idempotency, retries, and failure visibility.

#### Release tasks

1. Support staging dress rehearsal and production rollout verification.

### 2.5 AI and ML

#### Design tasks

1. Freeze MVP agent boundaries, model selection, thresholds, and fallback strategy.
2. Freeze prompt, evidence, and confidence output contracts.

#### Build tasks

1. Implement OCR preprocessing and VietOCR pipeline.
2. Implement classification, extraction, validation-support scoring, and confidence aggregation.
3. Implement structured outputs and error/fallback behavior for agent steps.

#### Test tasks

1. Create golden, messy, safety, and low-quality benchmark packs.
2. Validate extraction completeness, confidence behavior, disagreement handling, and reviewer override patterns.

#### Release tasks

1. Promote approved model and prompt bundles through staging to production.
2. Provide rollback targets and impacted-case identification logic.

### 2.6 Data and Contracts

#### Design tasks

1. Freeze shared JSON contracts, entity schemas, and evidence-link requirements.
2. Freeze annotation and feedback-loop design for post-MVP model improvement.

#### Build tasks

1. Implement schema migrations, event payload definitions, and artifact manifests.
2. Build dataset generation and lineage capture for training-ready outputs.

#### Test tasks

1. Validate schema compatibility and lineage completeness.
2. Validate evidence linkage from raw document to decision and audit.

#### Release tasks

1. Approve schema migration readiness and rollback compatibility.

### 2.7 Frontend Ops Workstation

#### Design tasks

1. Freeze screen inventory, navigation, and page-level action model.
2. Freeze role-based UI behavior and evidence comparison design.

#### Build tasks

1. Implement case list, case detail, document viewer, extraction review, validation panel, correction flow, escalation flow, and audit history view.
2. Integrate role-based action gating and error/empty/loading states.

#### Test tasks

1. Validate primary user journeys across ops, compliance, and fraud roles.
2. Validate evidence-linked correction and revalidation flows.

#### Release tasks

1. Support UAT and operational training walkthroughs.

### 2.8 Security and Identity

#### Design tasks

1. Freeze RBAC, secure upload, encryption, secret-handling, and audit-protection controls.
2. Freeze service-to-service auth and log protection rules.

#### Build tasks

1. Implement identity integration, role enforcement, secure artifact access, and secret delivery.
2. Implement upload scanning and quarantine handling.
3. Implement redaction, access-denied logging, and audit protection controls.

#### Test tasks

1. Run access-control, secure-upload, and sensitive-data-exposure tests.
2. Review privileged action enforcement and log handling behavior.

#### Release tasks

1. Approve MVP security baseline before pilot enablement.

### 2.9 DevOps and MLOps

#### Design tasks

1. Freeze environment topology, deployment flow, release governance, and observability plan.
2. Freeze initial alert thresholds, dashboard set, and rollback model.

#### Build tasks

1. Provision environments, CI/CD, secrets delivery, observability stack, and deployment automation.
2. Implement model registry controls, version promotion flow, and rollback hooks.

#### Test tasks

1. Run deployment rehearsals, backup/restore checks, and rollback exercises.
2. Validate dashboard coverage, alert routing, and operational runbooks.

#### Release tasks

1. Own production deployment execution and post-release observation window.

### 2.10 QA and UAT

#### Design tasks

1. Finalize test plan, fixture strategy, and release gates.
2. Finalize acceptance matrix per epic and per workflow.

#### Build tasks

1. Implement automated test suites and fixture packs.
2. Prepare UAT scripts and defect triage workflow.

#### Test tasks

1. Execute functional, integration, E2E, low-quality-document, review-flow, and security-sensitive test suites.
2. Run regression packs for rules, prompts, models, APIs, and UI workflows.

#### Release tasks

1. Issue formal QA sign-off or release block with severity rationale.

## 3. Milestones

| Milestone | Target Outcome | Exit Condition |
| --- | --- | --- |
| M1: Scope and Architecture Freeze | MVP scope and interface boundaries frozen | PRD, architecture, contracts, and delivery backlog approved |
| M2: Foundation Ready | environments, auth, persistence, workflow skeleton, contracts in place | staging foundation deployable and core schemas stable |
| M3: Core Processing Path Ready | end-to-end machine path works for MVP docs | intake through extraction, validation, and review task creation demo passes |
| M4: Review Workstation Ready | reviewers can process and correct cases | case list, case detail, evidence review, correction, escalation, and audit views usable |
| M5: Integrated MVP Feature Complete | backend, AI, UI, security, and audit integrated | all MVP user stories code-complete and integration-tested |
| M6: Hardening and UAT Complete | release candidate meets quality and control gates | QA gates, UAT sign-off, and pre-production checklist complete |
| M7: Pilot Go-Live | controlled production rollout starts | go-live checklist complete and named support coverage active |

## 4. Dependency Tracking

### Key upstream-to-downstream dependencies

1. Product scope freeze feeds:
   backend, frontend, AI, QA, and delivery sequencing.
2. Domain rules and compliance controls feed:
   validation logic, decision policy, human-review logic, prompts, QA scenarios, and release gates.
3. Solution architecture feeds:
   backend decomposition, data contracts, frontend integration, security boundaries, and DevOps setup.
4. Shared data contracts and schema freeze feed:
   backend APIs, AI outputs, persistence, frontend state models, and QA automation.
5. Security baseline feeds:
   backend auth, frontend role gating, DevOps secrets setup, and QA security tests.
6. DevOps staging readiness feeds:
   integration testing, UAT, model shadow validation, and rollback rehearsal.

### Dependency blockers to watch early

1. Unfrozen reason codes, enum values, or workflow states.
2. Late changes to document taxonomy or mandatory fields.
3. Missing external screening adapter plan.
4. Missing secure artifact-access pattern.
5. Unavailable staging environment or observability stack.
6. No approved low-quality and safety-case fixtures for AI and QA validation.

## 5. Critical Path

The MVP critical path is:

1. Freeze MVP scope, rules, controls, and contracts.
2. Stand up environments, auth baseline, persistence, and workflow skeleton.
3. Implement case intake, document storage, audit writes, and case state model.
4. Implement OCR, classification, extraction, validation, and review task creation for MVP documents.
5. Implement review workstation and correction/revalidation loop.
6. Integrate compliance gating and final decision routing with required human approvals.
7. Complete E2E testing, security validation, regression packs, and UAT.
8. Rehearse deployment, rollback, and incident support.
9. Release controlled pilot.

If any of the following slip, MVP slips:

1. contract freeze
2. staging readiness
3. OCR/extraction baseline readiness
4. review workstation readiness
5. compliance gate implementation
6. audit completeness and QA release gate

## 6. Suggested Sprint Plan

Assumption:
two-week sprints, with a 6-sprint MVP build plus a dedicated hardening/go-live phase.

### Sprint 0: Program Setup

1. Finalize epics, owners, and dependency log.
2. Freeze MVP scope, document list, and acceptance criteria.
3. Freeze contracts, initial schema model, and service boundaries.
4. Stand up development workflow, branching rules, and release cadence.

### Sprint 1: Platform Foundation

1. Environments, CI/CD, observability baseline, auth integration, and secrets setup.
2. PostgreSQL schema foundation, object storage, audit-event model, and workflow skeleton.
3. Frontend shell and role-aware navigation scaffold.

### Sprint 2: Intake and Case Control

1. Case creation, document registration, checksum/hash handling, and status retrieval.
2. Case list, case detail shell, upload UX, and initial audit view.
3. Secure upload handling, file validation, and quarantine logic.

### Sprint 3: AI Core Path

1. OCR preprocessing and VietOCR integration.
2. Classification, extraction, evidence refs, and confidence outputs.
3. Shared result retrieval and structured error handling.

### Sprint 4: Validation and Review Routing

1. Validation engine, cross-document rules, compliance state model, and decision pre-routing.
2. Review task generation, claim flow, and reviewer queue management.
3. Low-confidence, mismatch, and exception routing paths.

### Sprint 5: Review Workstation and Revalidation

1. Document viewer, extracted field review, issue panel, manual correction, escalation, and revalidation.
2. Audit history completion and role-based action gating.
3. Model and prompt benchmark pack stabilization.

### Sprint 6: MVP Integration Completion

1. Final decision flow, closure logic, downstream-ready outputs, and full E2E integration.
2. Security-sensitive behavior closure, access-control hardening, and runbook draft completion.
3. UAT dry run and defect burn-down start.

### Sprint 7: Hardening and Go-Live Preparation

1. Regression reruns, low-quality and failure-path validation, rollback rehearsal, and deployment rehearsal.
2. UAT completion, training materials, operational dashboard validation, and final go/no-go.

## 7. MVP Build Sequence

Build in this order:

1. Scope, rules, controls, and contracts
2. environments and security baseline
3. persistence, audit, and workflow backbone
4. intake APIs and upload flow
5. OCR and structured AI outputs
6. validation, compliance state, and routing
7. review tasking and reviewer workstation
8. correction, revalidation, and escalation
9. final decision and closure logic
10. hardening, UAT, release readiness, and pilot launch

Do not invert this sequence by building advanced model logic before:

1. evidence linkage
2. review workflow
3. audit completeness
4. secure access controls

## 8. Testing and Hardening Phase

### Hardening objectives

1. Remove silent failure paths.
2. Validate workflow correctness under retries, timeouts, and dependency failures.
3. Validate low-quality and contradictory document behavior.
4. Validate secure access, upload controls, audit completeness, and rollback readiness.

### Required hardening activities

1. Full regression pass across APIs, workflows, AI outputs, UI, and security controls.
2. Low-quality-document and messy-case pack execution.
3. Manual-review and specialist-escalation workflow testing.
4. Alert threshold tuning and dashboard verification.
5. Deployment rollback and model rollback rehearsal.
6. Backup, restore, and impacted-case identification rehearsal.
7. UAT execution with operations and compliance stakeholders.

## 9. Pre-Production Readiness Checklist

### Design and scope

1. MVP scope frozen and approved.
2. Open questions reviewed and either resolved or deferred with compensating control.
3. Architecture deviations documented and approved.

### Build readiness

1. APIs, schemas, and workflow states frozen for release candidate.
2. Staging mirrors production shape for critical dependencies.
3. Security baseline implemented:
   auth, RBAC, encryption, secure upload, secret delivery, log protection.

### Quality readiness

1. QA release gate passed.
2. UAT scripts approved.
3. Golden, messy, safety, and low-quality packs available and versioned.
4. Known defects triaged with owner, severity, and release disposition.

### Operational readiness

1. Dashboards and alerts validated.
2. Runbooks for top incidents approved.
3. On-call owners, escalation paths, and release observation window assigned.

## 10. Go-Live Readiness Checklist

1. Production deployment plan approved with named release owner.
2. Rollback plan approved for services, prompts, thresholds, and models.
3. Production secrets, certificates, and access policies verified.
4. Audit writes, evidence writes, and case retrieval validated in production-like rehearsal.
5. External screening and critical adapters verified or compensating review-only mode enabled.
6. Operations, compliance, and support teams briefed on pilot scope and escalation paths.
7. Monitoring and alert routing live and tested.
8. Release communications prepared.
9. Post-release observation window staffed.
10. Go/no-go decision recorded by product, engineering, security, QA, and operations.

## 11. Risks and Mitigations

| Risk | Delivery Impact | Mitigation |
| --- | --- | --- |
| Contract churn across teams | rework and integration delays | freeze enums, schemas, and workflow states by end of Sprint 0 |
| AI output instability | review UX and decision logic churn | use strict contracts, benchmark packs, and conservative thresholds |
| Staging not production-like | false confidence before launch | treat staging parity as a tracked milestone with owner |
| Screening adapter delay | regulated pilot blocked | build pending/review-required fallback and pilot with controlled scope only |
| Review UI arrives late | no safe operational path | place workstation on critical path from Sprint 2 onward |
| Security hardening deferred | release block near go-live | include auth, secure upload, and log protection in early sprints |
| Audit gaps discovered late | compliance and QA release block | implement audit events as part of core backend stories, not later polish |
| Too many concurrent workstreams | diffused ownership and slippage | assign one primary owner per workstream and track weekly dependency burn-down |

## 12. Scale-Stage Transition Plan

### Transition trigger

Move from MVP to scale-stage planning only after:

1. stable pilot operations over an agreed observation window,
2. acceptable defect and incident profile,
3. validated reviewer throughput,
4. no unresolved release-blocking control gaps,
5. approved KPI baseline for automation, review rate, and turnaround time.

### Scale-stage work packages

1. Expand supported document set and channels.
2. Add broader automation only where override and exception evidence is acceptable.
3. Introduce stronger model canarying, drift-triggered investigation, and retraining workflow.
4. Add richer reporting, SLA forecasting, and queue optimization.
5. Add regional resilience, broader workload isolation, and more advanced support coverage.

### Transition governance

1. Run a post-pilot retrospective with product, ops, compliance, QA, security, and engineering.
2. Re-prioritize the roadmap based on measured bottlenecks rather than design-time assumptions.
3. Promote scale work only after explicit approval that MVP controls remain intact.

## Recommended Delivery Stance

1. Treat contract freeze, review workstation readiness, and audit completeness as program-level gates.
2. Optimize for one complete safe path first, not parallel partial paths.
3. Keep model ambition behind operational safety, review usability, and release discipline.
4. Escalate blockers early:
   do not hide dependency slippage inside team-local sprint boards.

# Technical Design Document for Ops Agent

## Role

Senior cross-functional architect for a banking-grade Document Processing Agent.

## Objective

Provide one implementation-ready technical design document that consolidates product scope, architecture, AI workflow, backend, data, API, frontend, security, QA, and operations design for the Ops Agent MVP and its scale path.

## Assumptions

1. The system handles sensitive identity, financial, and compliance-relevant banking documents.
2. The first release is a controlled MVP with conservative automation boundaries and mandatory human review for all KYC approvals and high-risk cases.
3. Existing design artifacts in `docs/` remain the detailed source documents; this TDD is the implementation kickoff document and cross-reference hub.
4. The target stack is Python/FastAPI, event-driven orchestration, VietOCR-based OCR, PostgreSQL, S3-compatible storage, React/Next.js review UI, and audited banking controls.

## Deliverables

- Executive summary
- Scope
- Business context
- System architecture
- AI and agent workflow
- Backend design
- Data model
- API design
- Frontend design summary
- Security controls
- Auditability and compliance design
- Testing strategy summary
- Deployment and operations summary
- MVP scope
- Scale-stage architecture evolution
- Open questions
- Risks and mitigations

## Cross-Reference Sources

1. [ops-agent-prd.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ops-agent-prd.md)
2. [solution-architecture-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\solution-architecture-blueprint.md)
3. [ai-architecture.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ai-architecture.md)
4. [backend-service-decomposition.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\backend-service-decomposition.md)
5. [api-specification.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\api-specification.md)
6. [database-persistence-schema.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\database-persistence-schema.md)
7. [shared-data-contracts.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\shared-data-contracts.md)
8. [frontend-dashboard-functional-spec.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\frontend-dashboard-functional-spec.md)
9. [security-architecture-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\security-architecture-controls.md)
10. [compliance-risk-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\compliance-risk-controls.md)
11. [qa-engineering-test-strategy.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\qa-engineering-test-strategy.md)
12. [devops-mlops-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\devops-mlops-blueprint.md)

## 1. Executive Summary

Ops Agent is a banking operations platform for controlled document intake, OCR, classification, extraction, validation, review, compliance gating, and audited decision support. The design is intentionally conservative: deterministic rules and workflow state control govern regulated outcomes, AI components assist bounded subproblems, and human review remains mandatory for sensitive decisions.

The MVP focuses on one safe end-to-end path:

1. receive documents,
2. register evidence,
3. run OCR and structured extraction,
4. validate business and compliance requirements,
5. route uncertain or sensitive cases to human review,
6. persist full audit and evidence linkage,
7. expose case and review flows through an operations dashboard.

This document is the implementation kickoff reference. It summarizes the target design and points teams to the detailed specifications for schemas, prompts, APIs, QA, and controls.

## 2. Scope

### In scope

1. Case intake and document registration
2. Document storage and metadata registration
3. OCR using VietOCR with OpenCV preprocessing
4. Document classification and field extraction
5. Validation and cross-document consistency checks
6. Compliance state tracking and escalation triggers
7. Decision support with conservative automation boundaries
8. Human review workstation for correction, escalation, and closeout
9. Audit logging, evidence traceability, observability, and rollback-ready operations

### Out of scope for MVP

1. Broad channel expansion beyond the defined intake paths
2. Full autonomous KYC approval
3. Autonomous sanctions, AML, fraud, or rejection decisions
4. Multi-region active-active topology
5. Large-scale model retraining automation and broad experimentation framework

For product scope and acceptance detail, see [ops-agent-prd.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ops-agent-prd.md).

## 3. Business Context

The business problem is operationally expensive, slow, and error-prone banking document processing. Teams currently spend time collecting files, rekeying fields, checking consistency, validating document freshness, handling exceptions, and reconstructing decisions for audit and compliance review.

The design therefore optimizes for:

1. reduced manual document handling,
2. explicit workflow and exception visibility,
3. safe human-review routing,
4. strong auditability and evidence linkage,
5. measurable straight-through processing only where controls allow it.

Target users include operations reviewers, compliance analysts, fraud analysts, branch support, and back-office processors. Those personas and their flows are defined in [ops-agent-prd.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ops-agent-prd.md).

## 4. System Architecture

### 4.1 Logical architecture

```text
Users / Upstream Systems
        |
        v
API Gateway / WAF
        |
        v
FastAPI Control Plane
- case service
- review service
- workflow service
- audit access
        |
        +---------------------+
        |                     |
        v                     v
Temporal                Kafka / Redis + Celery
- orchestration         - async jobs
- timers                - OCR / extraction / validation tasks
- retries
        |
        +--------------------------------------------------+
        |              |              |                    |
        v              v              v                    v
OCR service      classification   validation         compliance / decision
- OpenCV         extraction       rules engine       policy gates
- VietOCR        confidence       cross-doc checks   escalation routing
        |
        +-------------------+--------------------------+
                            |                          |
                            v                          v
                PostgreSQL system of record       S3 / MinIO evidence store
                OpenSearch read model             prompt/model artifacts
                            |
                            v
                 Next.js review workstation
                            |
                            v
                    Observability and audit plane
```

### 4.2 Architectural stance

1. Keep a clear separation between control plane, worker plane, storage plane, and review UI.
2. Use PostgreSQL as the system of record for workflow state, decisions, review actions, and audit metadata.
3. Use S3/MinIO for raw and derived evidence artifacts.
4. Use OpenSearch as a read-optimized operational index only, not the source of truth.
5. Use Temporal for durable workflow orchestration and Celery/Kafka for bounded async compute.

For the full architecture and service boundaries, see [solution-architecture-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\solution-architecture-blueprint.md).

## 5. AI and Agent Workflow

### 5.1 Agent set

The MVP workflow uses the following bounded agents or service-aligned reasoning steps:

1. Ingestion Agent
2. OCR Agent
3. Layout Parsing Agent
4. Classification Agent
5. Extraction Agent
6. Validation Agent
7. Compliance Agent
8. Decision Agent
9. Audit Agent
10. Human Review Agent

### 5.2 Workflow sequence

1. Ingestion registers case and documents.
2. OCR preprocesses and extracts text and layout artifacts.
3. Classification determines document type or routes to review when uncertain.
4. Extraction produces field-level values with confidence and evidence references.
5. Validation applies deterministic rules and cross-document checks.
6. Compliance evaluates required control status and escalation conditions.
7. Decision selects auto-progress, review-required, escalate, fail, or close-ready status based on policy.
8. Human review corrects or escalates where required.
9. Audit captures every material action with version references.

### 5.3 AI decision framework

1. Use rules for schema validation, required fields, freshness, thresholds, and hard gating.
2. Use classical ML for classification, anomaly support, and confidence support where behavior is measurable and stable.
3. Use LLM-based reasoning only for bounded ambiguous interpretation or reviewer-assist tasks where deterministic methods are insufficient and outputs remain structured and evidence-backed.

### 5.4 Confidence and fallback

1. High confidence does not bypass policy gates.
2. Medium confidence triggers cross-checks or review-required routing.
3. Low confidence routes to human review.
4. Failed OCR, conflicting fields, missing mandatory evidence, or model disagreement never produce silent final decisions.

For agent boundaries, contracts, routing logic, and safe degradation, see [ai-architecture.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ai-architecture.md) and [prompt-system.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\prompt-system.md).

## 6. Backend Design

### 6.1 Service decomposition

The backend is organized around explicit service responsibilities:

1. `case-service`
   owns case creation, state retrieval, and document registration metadata.
2. `workflow-service`
   owns Temporal workflow orchestration and workflow-visible state transitions.
3. `review-service`
   owns review tasks, field corrections, escalations, revalidation requests, and close actions.
4. `audit-service`
   owns append-only audit event creation and retrieval.
5. `ai-worker-services`
   perform OCR, classification, extraction, and related compute steps without directly mutating workflow state.

### 6.2 Core backend rules

1. Workers never directly perform uncontrolled final case-state mutation.
2. Every material state transition is explicit, validated, and audited.
3. All retry behavior is bounded and visible.
4. Failures produce workflow-visible statuses, alerts, or DLQ records.

### 6.3 Case state machine

The current state model includes:

`received`, `stored`, `queued`, `processing`, `validated`, `review_required`, `in_review`, `corrected`, `approved`, `rejected`, `escalated`, `failed`, `closed`

Compliance state is tracked separately from workflow state to prevent false flattening of pending or partial compliance into completed workflows.

For the detailed service list and execution model, see [backend-service-decomposition.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\backend-service-decomposition.md).

## 7. Data Model

### 7.1 Core entities

The primary relational entities are:

1. `cases`
2. `documents`
3. `document_pages`
4. `ocr_runs`
5. `classification_results`
6. `extraction_results`
7. `validation_results`
8. `compliance_results`
9. `decision_results`
10. `review_tasks`
11. `field_corrections`
12. `escalations`
13. `audit_events`

### 7.2 Storage boundaries

1. PostgreSQL stores workflow state, review actions, decision metadata, result metadata, and audit metadata.
2. S3/MinIO stores raw files, rendered previews, OCR artifacts, model outputs, and evidence attachments.
3. OpenSearch stores derived read models and search indexes.

### 7.3 Data design requirements

1. Every derived output must link back to its source document or page.
2. Every critical result must include version metadata for rules, models, and prompts where applicable.
3. Evidence linkage must survive retries, revalidation, correction, and review cycles.

For schemas and persistence detail, see [database-persistence-schema.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\database-persistence-schema.md) and [shared-data-contracts.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\shared-data-contracts.md).

## 8. API Design

### 8.1 API principles

1. Case-centric resource naming
2. Explicit workflow-safe transitions
3. Machine-readable errors and reason codes
4. Async status visibility for long-running operations
5. Minimal but sufficient payloads for UI and integrations

### 8.2 Core MVP endpoints

1. `POST /v1/cases`
2. `GET /v1/cases/{case_id}`
3. `POST /v1/cases/{case_id}/documents`
4. `GET /v1/cases/{case_id}/documents/{document_id}`
5. `GET /v1/cases/{case_id}/results`
6. `GET /v1/review-tasks`
7. `POST /v1/review-tasks/{task_id}/claim`
8. `POST /v1/cases/{case_id}/field-corrections`
9. `POST /v1/cases/{case_id}/escalations`
10. `POST /v1/cases/{case_id}/revalidate`
11. `POST /v1/cases/{case_id}/close`
12. `GET /v1/cases/{case_id}/audit-events`

### 8.3 Contract requirements

1. Requests and responses must align with the shared JSON schemas.
2. Every result payload must carry status, reason codes, confidence where relevant, and evidence references where required.
3. Error responses must support retry-safe client behavior.

See [api-specification.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\api-specification.md) and [shared-data-contracts.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\shared-data-contracts.md).

## 9. Frontend Design Summary

### 9.1 Primary UI surfaces

1. Case list
2. Case detail
3. Document viewer
4. Extracted field review panel
5. Validation and issue panel
6. Manual correction flow
7. Escalation flow
8. Audit history view

### 9.2 UX stance

1. Optimize for operational clarity and reviewer speed.
2. Keep extracted data and source evidence side by side.
3. Make uncertainty, pending checks, and blocked actions visually explicit.
4. Restrict actions by role and case state.

The full functional spec is in [frontend-dashboard-functional-spec.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\frontend-dashboard-functional-spec.md).

## 10. Security Controls

### 10.1 Core security requirements

1. RBAC with least privilege by default
2. Secure upload validation, scanning, and quarantine
3. Encryption in transit and at rest
4. Service-to-service authentication
5. Protected secret delivery and rotation
6. Log redaction and audit protection

### 10.2 Security-sensitive boundaries

1. Raw documents and derived OCR artifacts are sensitive.
2. Review notes, compliance outcomes, and audit records are sensitive.
3. Internal service trust is not implicit; every service call is authenticated and authorized.
4. Unauthorized access attempts must be blocked and logged.

See [security-architecture-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\security-architecture-controls.md) for the control matrix and hardening roadmap.

## 11. Auditability and Compliance Design

### 11.1 Auditability requirements

1. Every material action creates an append-only audit event.
2. Every decision must be reproducible from persisted evidence, rules, version refs, and actor attribution.
3. Human corrections, escalations, and overrides must preserve old and new values with rationale.

### 11.2 Compliance requirements

1. Compliance status is separate from workflow status.
2. Pending external checks remain visibly pending.
3. Sanctions, AML, fraud, true-match, and rejection outcomes require human approval.
4. Incomplete document sets or failed critical validations block final compliant-ready status.

See [compliance-risk-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\compliance-risk-controls.md) and [banking-document-rules.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\banking-document-rules.md).

## 12. Testing Strategy Summary

The QA approach is layered:

1. unit tests for rules, validators, and state transitions,
2. contract tests for APIs and agent payloads,
3. component tests for OCR, extraction, validation, and decision behavior,
4. integration tests for workflow, storage, queueing, and audit,
5. end-to-end tests for operational journeys,
6. regression packs for models, prompts, rules, APIs, and UI,
7. security-sensitive and low-quality-document scenarios as first-class release criteria.

The MVP release gate blocks on:

1. silent high-risk automation,
2. missing audit completeness,
3. broken review routing,
4. access-control failures,
5. evidence-link failures,
6. unresolved severe defects.

See [qa-engineering-test-strategy.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\qa-engineering-test-strategy.md).

## 13. Deployment and Operations Summary

### 13.1 Environment model

1. local development
2. shared development
3. staging
4. production
5. optional DR

### 13.2 Operational design

1. CI/CD for services, workflows, prompts, models, and infrastructure
2. observable services with metrics, logs, traces, and dashboards
3. explicit rollback for services, prompts, thresholds, and models
4. alerting on availability, queue lag, audit write failure, evidence write failure, and model-quality degradation

### 13.3 MVP production stance

1. single primary region
2. controlled rollout
3. conservative thresholding
4. staffed observation window
5. review-heavy fallback mode when AI components degrade

See [devops-mlops-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\devops-mlops-blueprint.md) and [execution-delivery-plan.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\execution-delivery-plan.md).

## 14. MVP Scope

The MVP implements:

1. case intake and document registration,
2. support for the defined MVP document types,
3. VietOCR-based OCR pipeline,
4. classification, extraction, validation, and conservative routing,
5. review task creation and reviewer workstation,
6. correction, escalation, revalidation, and audited closeout,
7. security baseline, observability baseline, and release gating.

The MVP does not implement broad autonomous decisioning or large-scale automation expansion.

For precise product scope and priorities, see [ops-agent-prd.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ops-agent-prd.md).

## 15. Scale-Stage Architecture Evolution

After MVP stabilization and pilot evidence, the architecture can evolve by:

1. expanding document coverage and channels,
2. splitting services further where justified by throughput or ownership,
3. adding model canarying and richer drift automation,
4. increasing automation only where reviewer override and risk data support it,
5. adding regional resilience, broader reporting, and more advanced support operations.

The scale path must preserve the MVP control model:

1. explicit workflow state,
2. evidence-linked outputs,
3. human oversight for sensitive decisions,
4. auditable model and prompt governance.

## 16. Open Questions

1. Which exact external screening integrations are available for the first regulated pilot?
2. Which intake channels must be supported in MVP beyond direct upload?
3. What is the approved policy for review-only operation when external compliance dependencies degrade?
4. Which document classes, if any, are approved for limited straight-through processing in the first production release?
5. What retention and legal-hold variants apply by jurisdiction or business line?

## 17. Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Contract churn across backend, AI, and UI | rework and integration delays | freeze shared schemas and enums before broad implementation |
| AI confidence instability | unsafe routing or reviewer overload | use benchmark packs, conservative thresholds, and review-required defaults |
| Audit gaps discovered late | release block and compliance risk | implement audit as core infrastructure, not release polish |
| Review UX lags backend completion | no safe operational path | keep review workstation on the MVP critical path |
| Security hardening deferred | launch blocker | include auth, upload security, secret handling, and log protection in early sprints |
| External dependency degradation | blocked compliant completion | support pending/review-required fallback and visible degraded mode |
| Overbuilding scale concerns in MVP | delivery slip | keep MVP scoped to one complete safe path end to end |

## Recommended Implementation Stance

1. Treat this TDD as the kickoff design and the linked documents as the detailed implementation packs.
2. Freeze contracts, workflow states, and role boundaries before parallel team execution.
3. Build evidence linkage, review workflow, and audit completeness before attempting aggressive automation gains.
4. Keep MVP release decisions tied to QA, security, compliance, and operational readiness gates rather than code completion alone.

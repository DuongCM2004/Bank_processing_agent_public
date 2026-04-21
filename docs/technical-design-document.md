# Technical Design Document for Ops Agent

## Role

Senior cross-functional architect for a banking-grade Document Processing Agent.

## Objective

Provide one implementation-ready technical design document that consolidates product scope, architecture, AI workflow, backend, data, API, frontend, security, QA, and operations design for the Ops Agent MVP and its scale path.

## Assumptions

1. The system handles sensitive identity, financial, and compliance-relevant banking documents.
2. The first release is a controlled MVP with conservative automation boundaries and mandatory human review for all KYC approvals and high-risk cases.
3. Existing design artifacts in `docs/` remain the detailed source documents; this TDD is the implementation kickoff document and cross-reference hub.
4. The target stack is Python/FastAPI, LangGraph extraction orchestration, OpenAI GPT-4o or GPT-4o-mini Vision structured extraction, PostgreSQL, object storage, React/Next.js review UI, and audited banking controls.
5. The document extraction pipeline is inference-only. It does not include dataset preparation, model training, model testing, benchmarking, or model evaluation workstreams.

## Current Extraction Baseline

The canonical Documents module design is [production-llm-document-extraction-backend-spec.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\production-llm-document-extraction-backend-spec.md). That document supersedes older OCR-model or ML-training language in this documentation set.

Production extraction is implemented as:

1. upload document image or PDF,
2. store the raw file in object storage,
3. queue asynchronous extraction,
4. preprocess the image with Python and Pillow,
5. encode the image as base64 data URL,
6. call OpenAI GPT-4o or GPT-4o-mini Vision for OCR-like visual reading and semantic JSON extraction,
7. enforce a strict Pydantic or JSON Schema contract,
8. retry once on schema validation failure,
9. normalize into an editable table,
10. require manual review,
11. persist only approved reviewed data,
12. write an audit trail and expose UUID search.

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

Ops Agent is a banking operations platform for controlled document intake, LLM-based structured extraction, validation, manual review, persistence, and audited decision support. The design is intentionally conservative: workflow state control governs regulated outcomes, GPT-4o Vision is used only for bounded structured extraction, and human review remains mandatory before extracted data becomes authoritative.

The MVP focuses on one safe end-to-end path:

1. receive documents,
2. register evidence,
3. preprocess document images,
4. run GPT-4o Vision structured extraction with strict JSON schema enforcement,
5. validate and retry once when schema validation fails,
6. route extracted fields to manual review,
7. persist only approved reviewed data,
8. preserve audit and UUID traceability,
9. expose document review flows through an operations dashboard.

This document is the implementation kickoff reference. It summarizes the target design and points teams to the detailed specifications for schemas, prompts, APIs, QA, and controls.

## 2. Scope

### In scope

1. Case intake and document registration
2. Document storage and metadata registration
3. image/PDF preprocessing with Python and Pillow
4. Vision LLM extraction using OpenAI GPT-4o or GPT-4o-mini
5. strict schema validation and one bounded retry
6. normalization into editable table format
7. manual review with edit, approve, and reject actions
8. approved-only persistence into production tables
9. audit logging, UUID search, evidence traceability, observability, and rollback-ready operations

### Out of scope for MVP

1. Broad channel expansion beyond the defined intake paths
2. Full autonomous KYC approval
3. Autonomous sanctions, AML, fraud, or rejection decisions
4. Multi-region active-active topology
5. Any dataset preparation, model training, model testing, benchmarking, or evaluation workflow for extraction

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
LangGraph               Redis / Celery or background workers
- extraction graph      - async jobs
- validation routing    - preprocessing / extraction / review tasks
- one retry
        |
        +--------------------------------------------------+
        |              |              |                    |
        v              v              v                    v
Preprocessing    LLM extraction   validation         review / persistence
- Pillow         GPT-4o Vision    Pydantic/JSON     approval gates
- base64 image   strict JSON      schema checks     audit routing
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
5. Use LangGraph for extraction orchestration and Celery, Redis Queue, or background workers for bounded async execution.

For the full architecture and service boundaries, see [solution-architecture-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\solution-architecture-blueprint.md).

## 5. AI and Agent Workflow

### 5.1 Agent set

The MVP workflow uses the following bounded agents or service-aligned reasoning steps:

1. Document Upload Service
2. Preprocessing Service
3. LangGraph Extraction Orchestrator
4. LLM Adapter
5. Validation Layer
6. Retry Handler
7. Normalization Layer
8. Manual Review Service
9. Persistence Layer
10. Audit Trail Service
11. UUID Search Service

### 5.2 Workflow sequence

1. Ingestion registers case and documents.
2. Preprocessing validates and encodes document images.
3. LangGraph calls GPT-4o Vision for strict JSON extraction.
4. Validation enforces the identity-document schema.
5. Retry runs once when schema validation fails.
6. Normalization flattens structured JSON into table rows.
7. Human review edits, approves, or rejects the extracted data.
8. Persistence writes only approved reviewed data.
9. Audit captures every material action with UUID and version references.

### 5.3 AI decision framework

1. Use rules for schema validation, required fields, freshness, thresholds, and hard gating.
2. Use GPT-4o Vision as the primary bounded extraction engine for identity-document OCR-like reading and semantic field extraction.
3. Do not use LLM output for final approval, rejection, or compliance disposition.

### 5.4 Validation and fallback

1. Schema-valid output does not bypass manual review.
2. Missing or uncertain values remain `null`.
3. Invalid structured output triggers one retry with a stricter prompt.
4. Failed preprocessing, schema mismatch, invalid JSON, or repeated validation failure never produce silent final decisions.

For agent boundaries, contracts, routing logic, and safe degradation, see [ai-architecture.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ai-architecture.md) and [prompt-system.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\prompt-system.md).

## 6. Backend Design

### 6.1 Service decomposition

The backend is organized around explicit service responsibilities:

1. `case-service`
   owns case creation, state retrieval, and document registration metadata.
2. `workflow-service`
   owns async job dispatch and workflow-visible document status transitions.
3. `review-service`
   owns review tasks, field corrections, escalations, revalidation requests, and close actions.
4. `audit-service`
   owns append-only audit event creation and retrieval.
5. `document-extraction-workers`
   perform preprocessing, GPT-4o Vision extraction, schema validation, retry, and normalization without directly mutating approved business data.

### 6.2 Core backend rules

1. Workers never directly perform uncontrolled final case-state mutation.
2. Every material state transition is explicit, validated, and audited.
3. All retry behavior is bounded and visible.
4. Failures produce workflow-visible statuses, alerts, or DLQ records.

### 6.3 Case state machine

The current state model includes:

`uploaded`, `queued`, `preprocessing`, `extracting`, `validating`, `retrying`, `extracted`, `in_review`, `approved`, `rejected`, `persisted`, `failed`

Compliance state is tracked separately from workflow state to prevent false flattening of pending or partial compliance into completed workflows.

For the detailed service list and execution model, see [backend-service-decomposition.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\backend-service-decomposition.md).

## 7. Data Model

### 7.1 Core entities

The primary relational entities are:

1. `cases`
2. `documents`
3. `document_pages`
4. `extraction_runs`
5. `extracted_data`
6. `review_logs`
7. `audit_events`

### 7.2 Storage boundaries

1. PostgreSQL stores workflow state, review actions, decision metadata, result metadata, and audit metadata.
2. Object storage stores raw files, rendered previews, preprocessed images, raw LLM responses, normalized payloads, and evidence attachments.
3. OpenSearch stores derived read models and search indexes.

### 7.3 Data design requirements

1. Every derived output must link back to its source document or page.
2. Every extraction run must include model name, prompt version, schema version, attempt count, raw LLM artifact URI, and validation errors where applicable.
3. Evidence and audit linkage must survive retries, correction, review, approval, rejection, and production persistence.

For schemas and persistence detail, see [database-persistence-schema.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\database-persistence-schema.md) and [shared-data-contracts.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\shared-data-contracts.md).

## 8. API Design

### 8.1 API principles

1. Case-centric resource naming
2. Explicit workflow-safe transitions
3. Machine-readable errors and reason codes
4. Async status visibility for long-running operations
5. Minimal but sufficient payloads for UI and integrations

### 8.2 Core MVP endpoints

1. `POST /documents/upload`
2. `GET /documents/{uuid}/status`
3. `GET /documents/{uuid}/extraction`
4. `POST /documents/{uuid}/review`
5. `GET /audit/{uuid}`

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
3. component tests for preprocessing, extraction, validation, and review behavior,
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
3. Pillow-based preprocessing and base64 image transport,
4. GPT-4o Vision structured JSON extraction,
5. strict schema validation and one retry,
6. review task creation and editable extraction table,
7. approved-only persistence,
8. security baseline, observability baseline, audit trail, and UUID search.

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
| LLM schema or hallucination risk | invalid or unsupported extracted fields | use strict JSON schema, null-for-unknown prompting, one retry, manual review, and approved-only persistence |
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

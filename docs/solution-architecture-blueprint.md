# Solution Architecture Blueprint for Ops Agent

## Role

Solution Architect for a banking-grade Document Processing Agent.

## Objective

Create a coherent, end-to-end technical blueprint that aligns product, AI, backend, data, frontend, security, and operations into one implementable system design for banking document workflows.

## Assumptions

1. MVP scope remains limited to retail `kyc_onboarding`, `income_verification`, `bank_statement_analysis`, and `loan_document_intake`.
2. The platform is an internal operations system, not a customer-facing banking core.
3. VietOCR is the mandated OCR engine and remains the only primary OCR path.
4. Human review is mandatory for regulated, high-risk, ambiguous, escalated, or exception-based cases.
5. Product, banking-domain, compliance, and AI architecture documents already define the operating rules; this document integrates them into a single delivery blueprint.

## Deliverables

- Architecture goals
- Major system components
- Component responsibilities
- Data flow
- Integration flow
- Human review integration points
- Audit and observability architecture
- Security-sensitive boundaries
- Dependencies
- MVP and scale guidance
- Risks and mitigations

## 1. System Architecture

### 1.1 Architecture goals

1. Build a banking-grade document processing platform that is safe, auditable, and practical for real operations teams.
2. Separate business control, workflow orchestration, AI processing, persistence, and review UI so teams can work in parallel.
3. Keep the MVP narrow enough to deliver quickly without locking the platform into a dead-end architecture.
4. Make human review, audit traceability, and compliance gating first-class parts of the design rather than afterthoughts.
5. Ensure deployment topology supports resilience, rollback, and future scale without over-fragmenting the initial release.

### 1.2 Logical end-to-end architecture

```text
External Sources
  -> Branch portal / Ops portal / Secure email / Upstream APIs
  -> API Gateway (Kong or Nginx)
  -> AuthN/AuthZ (Keycloak OAuth2 / OIDC)
  -> FastAPI platform services
     -> ingestion-service
     -> case-service
     -> workflow-service
     -> review-service
     -> compliance-service
     -> decision-service
     -> audit-service
  -> Temporal workflow engine
  -> Kafka event bus
  -> Celery worker pools
     -> OCR workers (VietOCR + OpenCV + PyTorch)
     -> layout workers
     -> classification workers
     -> extraction workers
     -> validation workers
  -> Shared data plane
     -> S3 / MinIO for raw docs and evidence artifacts
     -> PostgreSQL for transactional metadata
     -> OpenSearch for operational search and audit indexing
     -> Weaviate for semantic retrieval where explicitly allowed
  -> Human review workstation (Next.js / React)
  -> Observability and security plane
     -> ELK
     -> Prometheus / Grafana
     -> OpenTelemetry
     -> immutable audit storage
```

### 1.3 Architectural principles

1. Keep the system modular by separating orchestration, compute, transactional APIs, and human review.
2. Keep the MVP thin by building a small number of services around the most important domain boundaries.
3. Put rules and compliance gates ahead of ML and LLM behavior.
4. Treat every material system step as an auditable event.
5. Make all external integrations replaceable through stable service interfaces.

### 1.4 Deployment-oriented view

1. Edge layer
   API gateway, TLS termination, request filtering, auth token validation, and rate limiting.
2. Control plane
   FastAPI services for cases, workflow control, review actions, compliance status, and audit access.
3. Worker plane
   Celery-backed compute services for OCR, layout parsing, classification, extraction, and validation tasks.
4. Orchestration plane
   Temporal for durable long-running workflow state, timers, human-review pauses, and retries.
5. Data plane
   PostgreSQL for transactional state, S3 / MinIO for evidence artifacts, OpenSearch for read-optimized search and audit indexing, optional Weaviate for restricted semantic retrieval.
6. Observability and security plane
   Logs, metrics, traces, alerting, secrets, IAM integration, and immutable audit retention.

### 1.5 MVP architecture boundaries

#### Build in MVP

1. `api-gateway`
2. `auth-service` integration with Keycloak
3. `ingestion-service`
4. `case-service`
5. `workflow-service`
6. `ocr-service`
7. `classification-service`
8. `extraction-service`
9. `validation-service`
10. `compliance-service`
11. `decision-service`
12. `review-service`
13. `audit-service`
14. `frontend-review-app`

#### Defer to scale phase

1. multi-region deployment
2. active-active failover
3. real-time fraud graph enrichment
4. broad semantic retrieval usage
5. advanced statement analytics
6. corporate ownership workflows

### 1.6 Key architecture trade-offs

1. Microservices vs delivery speed
   Use real service boundaries, but keep MVP deployable as a small platform estate rather than a sprawl of independently operated services.
2. Temporal plus Kafka plus Celery
   This adds operational complexity, but gives clear separation:
   Temporal for stateful orchestration, Kafka for domain events, Celery for compute execution.
3. Rules-first over AI-first
   This reduces novelty and some automation reach, but improves auditability, predictability, and compliance safety.
4. PostgreSQL as source of truth with OpenSearch as read model
   This avoids stale-search corruption of workflow truth at the cost of maintaining indexing pipelines.

## 2. Major System Components and Responsibilities

| Component | Purpose | Primary owner | Supporting teams |
|---|---|---|---|
| API Gateway | ingress, routing, auth policies, rate limits | Platform / DevOps | Security |
| Keycloak config | identity, SSO, RBAC | Security Platform | Frontend, Backend |
| Ingestion service | upload, checksum, storage registration | Backend | Security, Ops |
| Case service | case metadata, state APIs | Backend | Product |
| Workflow service / Temporal | orchestration and retry logic | Backend Platform | AI, Review |
| OCR service | OpenCV preprocessing, VietOCR inference | AI Platform | Infrastructure |
| Layout service | structural segmentation | AI Platform | Backend |
| Classification service | document type prediction | AI / ML | Product, QA |
| Extraction service | field extraction + evidence | AI / ML | Banking Domain, QA |
| Validation service | deterministic and cross-document rules | Backend + Rules | Banking Domain |
| Compliance service | KYC/AML control statuses and gates | Compliance Engineering | Compliance, Risk |
| Decision service | routing and automation boundaries | Backend + Product | Compliance, AI |
| Review service | reviewer tasks and manual actions | Backend | Frontend, Ops |
| Audit service | append-only events and trace access | Platform Engineering | Compliance, Audit |
| PostgreSQL | system-of-record metadata | Data Platform | Backend |
| S3 / MinIO | raw docs and artifacts | Data Platform | Security |
| OpenSearch | operational search and audit indexing | Data Platform | Platform |
| Weaviate | semantic retrieval store | AI Platform | Data Platform |
| Frontend review app | workstation UI | Frontend | Product, Ops |
| Observability stack | logs, metrics, traces, alerting | SRE / Platform | All teams |
| Rules / policy packs | business and compliance logic | Compliance + Product | Banking Domain, Backend |

### 2.1 Team interface rule

Each team owns its service boundary and schema versioning. Cross-team dependencies must occur through:

1. versioned API contracts,
2. versioned event schemas,
3. versioned artifact references,
4. explicit ownership in runbooks.

### 2.2 Responsibility summary by layer

1. Channel and intake layer
   Accepts documents and metadata from branch, ops, email, or upstream APIs and turns them into controlled cases.
2. Workflow and decision layer
   Controls state transitions, orchestration, retries, compliance gates, escalation, and case closure.
3. AI processing layer
   Produces OCR, layout, classification, extraction, and validation-support outputs with evidence and version metadata.
4. Review and operations layer
   Gives analysts case queues, document viewers, correction tools, escalation actions, and audit visibility.
5. Data and observability layer
   Stores raw evidence, transactional state, read models, audit events, logs, metrics, and traces.

## 3. Data Flow Map

### 3.1 Primary data flow

1. User or upstream system submits document bundle through gateway.
2. Ingestion service stores raw files in S3 / MinIO and persists case/document metadata in PostgreSQL.
3. Ingestion service emits `document.received`.
4. Workflow service starts a Temporal case workflow.
5. OCR service retrieves document pages, preprocesses with OpenCV, runs VietOCR, and writes OCR artifacts to S3.
6. Layout service reads page images and OCR blocks, computes document structure, and writes layout artifacts.
7. Classification service reads OCR/layout features, classifies document type, and persists result.
8. Extraction service applies deterministic extraction first and optional bounded fallback second; field outputs and evidence refs are stored.
9. Validation service executes field, freshness, and cross-document rules and writes validation results.
10. Compliance service updates control statuses and raises escalations where necessary.
11. Decision service aggregates all upstream outputs and chooses `auto_process`, `cross_check`, `human_review`, or `specialist_escalation`.
12. Review service creates manual tasks when required.
13. Human reviewer corrects fields, approves, rejects, or escalates.
14. Workflow service revalidates and closes only after required controls are completed.
15. Audit service records all events and indexes them into search.

### 3.2 Artifact storage model

| Artifact | Store | Retention role |
|---|---|---|
| Raw uploaded document | S3 / MinIO | system of record for source evidence |
| Derived page images | S3 / MinIO | OCR and review evidence |
| OCR output | S3 / MinIO + PostgreSQL refs | traceability and replay |
| Layout output | S3 / MinIO + PostgreSQL refs | extraction evidence |
| Extraction output | PostgreSQL + S3 evidence | downstream consumption |
| Validation results | PostgreSQL | decisioning and audit |
| Compliance control results | PostgreSQL | gating and examination |
| Audit events | PostgreSQL + immutable store + OpenSearch index | reconstruction and audit |
| Prompt/response artifacts | encrypted S3 | explainability and model governance |

### 3.3 Data state separation

Keep data in four clearly separated zones:

1. source evidence zone
2. derived AI artifact zone
3. transactional metadata zone
4. audit and observability zone

This separation prevents accidental overwrites and simplifies retention policy enforcement.

## 4. Integration Blueprint

### 4.1 Integration patterns

| Integration type | Pattern | Use case |
|---|---|---|
| External client to platform | synchronous REST via gateway | upload, case status, review actions |
| Internal service to service | synchronous REST for command/query | metadata updates, task operations |
| Async domain events | Kafka topics | workflow progression, audit fan-out, alerts |
| Long-running orchestration | Temporal activities and signals | retries, waits, human review |
| Artifact exchange | signed S3 object refs | OCR, layout, extraction evidence |

### 4.2 Required internal interfaces

#### `ingestion-service`

- `POST /v1/cases`
- `POST /v1/cases/{case_id}/documents`
- emits `document.received`

#### `workflow-service`

- `POST /internal/workflows/start`
- `POST /internal/workflows/{case_id}/signal-review`
- consumes and emits workflow state events

#### `ocr-service`

- `POST /internal/ocr/jobs`
- returns artifact refs and OCR confidence

#### `classification-service`

- `POST /internal/classification/jobs`

#### `extraction-service`

- `POST /internal/extraction/jobs`

#### `validation-service`

- `POST /internal/validation/jobs`

#### `compliance-service`

- `POST /internal/compliance/evaluate`
- `POST /internal/compliance/escalate`

#### `decision-service`

- `POST /internal/decision/evaluate`

#### `review-service`

- `GET /v1/review-tasks`
- `POST /v1/review-tasks/{task_id}/claim`
- `POST /v1/cases/{case_id}/field-corrections`
- `POST /v1/cases/{case_id}/escalations`
- `POST /v1/cases/{case_id}/revalidate`
- `POST /v1/cases/{case_id}/close`

### 4.3 External integrations

| External dependency | Interface pattern | MVP requirement |
|---|---|---|
| Keycloak | OIDC/OAuth2 | Must-have |
| S3 / MinIO | object API | Must-have |
| Email ingestion adapter | controlled mailbox poller / webhook | Should-have for MVP if email intake required |
| OFAC / sanctions screening | sync or async adapter | Must-have before regulated pilot |
| AML / fraud alert source | async integration | Should-have for pilot, must-have before production |
| LOS / onboarding system | API or event handoff | Beta |
| SIEM | log forwarding | Must-have before production |

### 4.4 Interface boundary rule

No service may read another service's private tables directly. Shared access occurs only through:

1. public APIs,
2. published events,
3. artifact refs,
4. approved read models such as OpenSearch.

### 4.5 End-to-end integration flow

1. Backend control services receive requests through the gateway and persist case intent in PostgreSQL.
2. Workflow service starts or advances the Temporal case workflow and dispatches compute steps through Celery and or Kafka.
3. AI services fetch source artifacts from S3 / MinIO, produce derived artifacts, and persist result metadata back through their owning services.
4. Validation, compliance, and decision services combine deterministic rules, upstream AI outputs, and workflow context to determine next routing action.
5. Review service exposes reviewer tasks and case details to the Next.js UI using backend APIs and approved read models.
6. Audit service and observability components receive event fan-out from workflow and service actions without becoming the system-of-record for case state.

### 4.6 Human review integration points

1. Post-intake exception review
   Triggered when upload, file checks, or document registration fail policy or technical checks.
2. Post-extraction review
   Triggered when mandatory fields are missing, evidence is weak, or classification is uncertain.
3. Post-validation review
   Triggered when business rules fail, cross-document mismatches exist, or confidence falls below automation thresholds.
4. Compliance specialist review
   Triggered by sanctions, PEP, AML, identity discrepancy, or policy-exception conditions.
5. Fraud specialist review
   Triggered by tampering suspicion, duplicate document indicators, inconsistent identity, or anomaly flags.
6. Final approval or closure review
   Required for KYC approval in MVP and any rejection, override, or escalated-case closure.

## 5. Audit, Observability, and Security-Sensitive Boundaries

### 5.1 Audit architecture

1. Every material action creates an append-only audit event:
   intake, storage, workflow start, OCR completion, extraction, validation, review claim, correction, escalation, revalidation, approval, rejection, and closure.
2. Audit service stores canonical audit records in PostgreSQL and forwards indexed copies to OpenSearch for operational retrieval.
3. Audit events must carry:
   `case_id`, `document_id` where relevant, `actor_type`, `actor_id`, `action`, `timestamp`, `reason_code`, `trace_id`, and version references for rules, models, or prompts when applicable.
4. Audit storage is distinct from mutable workflow tables so history is not rewritten by later case updates.

### 5.2 Observability architecture

1. Application logs
   Centralized into ELK or equivalent, correlated by `trace_id`, `case_id`, and service name.
2. Metrics
   Exposed through Prometheus for service health, workflow latency, queue depth, retry counts, review backlog, and AI quality indicators.
3. Distributed tracing
   OpenTelemetry traces span gateway, FastAPI services, Temporal activities, worker jobs, database calls, and storage operations.
4. Operational dashboards
   Separate views for platform health, review-queue health, AI pipeline health, and compliance backlog.
5. Alerting
   Triggered on service outage, queue lag, stuck workflows, audit-write failure, evidence-write failure, security violations, and material shifts in review or exception rates.

### 5.3 Security-sensitive boundaries

1. Untrusted input boundary
   All files and metadata entering through channel adapters are treated as untrusted until validated, scanned, and registered.
2. Identity and access boundary
   Gateway and backend services enforce OAuth2 / OIDC identity, RBAC, and least-privilege actions; UI visibility follows the same role constraints.
3. Evidence boundary
   Raw documents and derived artifacts live in encrypted object storage with controlled access paths; direct public access is prohibited.
4. Service-to-service boundary
   Internal APIs and workers use scoped credentials and encrypted transport; no shared superuser identity across services.
5. Audit boundary
   Audit records are append-only and protected from ordinary service mutation paths.
6. Model and prompt boundary
   Model artifacts, prompt templates, and confidence thresholds are treated as controlled production assets, not ad hoc runtime configuration.

## 6. Non-Functional Requirements

### 6.1 Reliability

1. No single document-processing failure may lose the case or source file.
2. All workflows must be resumable after service restart.
3. Processing tasks must be idempotent by `case_id`, `document_id`, `trace_id`, and step version.

### 6.2 Availability

#### MVP

1. Platform target availability: `99.5%` for internal operations hours.
2. Manual fallback must exist for all critical workflows.

#### Scale

1. Platform target availability: `99.9%+`
2. Planned HA for PostgreSQL, Kafka, Temporal, and object storage

### 6.3 Performance

1. Upload acknowledgment under 2 seconds for standard files.
2. OCR kickoff under 30 seconds from document registration.
3. p95 end-to-end processing under 10 minutes for standard single-document cases in MVP.
4. Human review screens load core case bundle under 3 seconds from cache/search index.

### 6.4 Security

1. TLS in transit for all network calls.
2. AES-256 equivalent encryption at rest for object storage and database volumes.
3. RBAC enforced through Keycloak tokens and service-level authorization.
4. Least-privilege credentials for every service.
5. Prompt and model artifacts treated as sensitive operational records.

### 6.5 Auditability

1. Every material action must produce an immutable audit event.
2. Every AI decision must be reproducible to model/rule/prompt version and evidence refs.
3. Pending compliance checks must never be hidden from users or downstream systems.

### 6.6 Scalability

1. Compute-heavy services scale horizontally by queue depth.
2. API services remain stateless.
3. Artifact storage scales independently from metadata storage.

### 6.7 Maintainability

1. Each service has its own deployment unit and runbook.
2. Shared schemas are versioned and contract-tested.
3. Rule packs and prompt templates are version-controlled separately from code when practical.

## 7. Dependencies

### 7.1 Business dependencies

1. Product workflow definitions
2. Banking document rule packs
3. Compliance control pack
4. queue ownership and SLA definitions from operations

### 7.2 Technical dependencies

1. Keycloak environment
2. PostgreSQL
3. S3 / MinIO
4. Kafka
5. Redis
6. Temporal
7. OpenSearch
8. Weaviate
9. GPU-enabled OCR worker environment

### 7.3 Team dependencies

#### Role dependency map

| Role | Depends on | Feeds |
|---|---|---|
| Product Manager | not explicitly upstream-dependent in this map | Solution Architect, AI Architect, Frontend Engineer, Project Manager |
| Banking Domain Expert | not explicitly upstream-dependent in this map | Product Manager, AI Architect, ML Engineer, QA Engineer, Compliance & Risk Specialist |
| Compliance & Risk Specialist | not explicitly upstream-dependent in this map | Product Manager, Solution Architect, AI Architect, Backend Engineer, Security Engineer, QA Engineer |
| Solution Architect | Product Manager, Banking Domain Expert, Compliance & Risk Specialist | Backend Engineer, Frontend Engineer, Data Engineer, Security Engineer, DevOps/MLOps Engineer, Project Manager |
| AI Architect | Product Manager, Banking Domain Expert, Compliance & Risk Specialist, Solution Architect | Prompt Engineer, ML Engineer, Backend Engineer, QA Engineer |
| Prompt Engineer | AI Architect, Banking Domain Expert, Compliance & Risk Specialist | Backend Engineer, QA Engineer, ML Engineer |
| ML Engineer | AI Architect, Banking Domain Expert, Data Engineer, Prompt Engineer | Backend Engineer, DevOps/MLOps Engineer, QA Engineer |
| Data Engineer | Solution Architect, AI Architect, ML Engineer | ML Engineer, Backend Engineer, QA Engineer, DevOps/MLOps Engineer |
| Backend Engineer | Solution Architect, AI Architect, Product Manager, Compliance & Risk Specialist, Security Engineer | Frontend Engineer, QA Engineer, DevOps/MLOps Engineer |
| Frontend Engineer | Product Manager, Solution Architect, Backend Engineer | QA Engineer |
| Security Engineer | Solution Architect, Backend Engineer, Compliance & Risk Specialist | Backend Engineer, DevOps/MLOps Engineer, QA Engineer |
| QA Engineer | almost all prior roles | Project Manager, Product Manager, Engineering team |
| DevOps / MLOps Engineer | Backend Engineer, ML Engineer, Security Engineer, Solution Architect | Project Manager, Engineering team |
| Project Manager | all major roles for planning and tracking | delivery planning, tracking, and execution governance |

#### Delivery interpretation

1. Product Manager sets business scope and workflow priority, then feeds architecture, AI, UX, and planning.
2. Banking Domain Expert and Compliance & Risk Specialist refine what is operationally and regulatorily acceptable before engineering design hardens.
3. Solution Architect converts product, domain, and compliance inputs into the cross-team system blueprint.
4. AI Architect converts business and solution constraints into the agent, model, and orchestration design consumed by Prompt, ML, Backend, and QA.
5. Backend, Frontend, Data, Security, and DevOps/MLOps are downstream implementers with shared interfaces but distinct ownership.
6. QA is intentionally downstream of almost every role because test strategy must validate the combined effect of product, business rules, compliance, AI behavior, backend state handling, UI review flow, and security controls.
7. Project Manager depends on upstream role outputs to sequence work, surface blockers, and manage delivery.

## 8. Implementation Sequencing

### 8.1 Sequence by release

#### MVP

1. shared schemas and case state model
2. gateway, auth, and core metadata services
3. object storage and PostgreSQL setup
4. ingestion and audit services
5. Temporal workflow and Kafka backbone
6. VietOCR OCR service and OpenCV preprocessing
7. deterministic classification and extraction for in-scope documents
8. validation and compliance services
9. decision service
10. reviewer UI
11. pilot observability dashboards and alerting

#### Beta

1. classical ML classification improvements
2. LLM bounded fallback path
3. email ingestion
4. downstream LOS / onboarding integrations
5. supervisor dashboards
6. stronger compliance and fraud adapters

#### Scale

1. HA and failover hardening
2. multi-team / multi-region configuration
3. advanced analytics and broader document taxonomy
4. automated drift monitoring and shadow testing pipelines

### 8.2 Parallelization guidance

These tracks can run in parallel after shared schemas are stable:

1. Backend core services
2. AI OCR / extraction pipeline
3. Frontend review workstation
4. Platform / SRE environment and observability
5. Security / IAM / secrets

## 9. Technical Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Over-designed MVP with too many services too early | slows delivery and integration | keep service count logical but deployable in one repo or small mono-platform initially |
| VietOCR quality variance on low-quality scans | extraction degradation | aggressive OpenCV preprocessing, region re-OCR, human fallback |
| Workflow complexity across Temporal, Kafka, and Celery | operational burden | clear separation: Temporal for orchestration, Kafka for events, Celery for compute only |
| Hidden coupling between services through shared DB reads | brittle architecture | enforce API/event-only boundaries |
| Compliance status not treated as a hard gate | unsafe automation | dedicated compliance service and explicit control status model |
| Model and prompt drift | silent quality decline | version registry, shadow tests, rollback, override monitoring |
| Human review UX too weak for real operations | low adoption, unsafe overrides | ship viewer, evidence refs, audit trace, and correction flows early |
| Search/index inconsistency | reviewers see stale state | PostgreSQL remains source of truth; search is read-optimized only |
| Dependency sprawl in MVP | difficult support model | defer non-essential adapters and advanced retrieval features |

## 10. Architecture Summary

The design is implementable if the team accepts two constraints:

1. MVP is a narrow operational wedge, not a universal banking automation platform.
2. Compliance and audit requirements shape architecture as much as AI performance does.

## 11. MVP Architecture and Scale-Stage Evolution

### 11.1 MVP architecture

1. Prefer one deployable platform repository with multiple services over a fragmented microservice estate.
2. Use only the minimum set of agents and workflows needed for retail onboarding and income verification.
3. Keep LLM usage off by default unless a bounded fallback is explicitly approved.
4. Ship human review and audit visibility before optimization work.
5. Prioritize:
   gateway, auth integration, case and ingestion services, workflow orchestration, OCR path, validation/compliance/decision services, review UI, and audit pipeline.

### 11.2 Scale-stage evolution

1. Split services into independently scalable domains only when queue depth, ownership, or release cadence justify it.
2. Add more document types through schema/rule packs, not by rewriting the core pipeline.
3. Expand retrieval, ML scoring, and downstream integrations after the operational loop is stable.
4. Add HA and DR controls for PostgreSQL, Kafka, Temporal, and object storage before broad enterprise rollout.
5. Introduce shadow model evaluation, drift monitoring, and controlled canary release for model and prompt changes.

### 11.3 Scale-stage trade-offs

1. More service isolation improves team autonomy and scaling, but increases platform and integration overhead.
2. More AI sophistication may reduce manual effort, but raises governance, explainability, and regression-testing costs.
3. More downstream integrations improve automation reach, but increase failure modes and reconciliation complexity.

## 12. Recommended Architectural Stance

The coherent architecture for Ops Agent is:

1. thin but real service boundaries,
2. durable workflow orchestration,
3. evidence-first AI processing,
4. compliance gating as a first-class subsystem,
5. human review as part of the core design rather than a fallback afterthought.

That gives the teams a blueprint that is implementable for MVP and extensible for scale without bloating the first release.

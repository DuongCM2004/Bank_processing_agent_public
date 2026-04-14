# DevOps and MLOps Blueprint for Ops Agent

## Role

DevOps / MLOps Engineer for a banking-grade Document Processing Agent.

## Objective

Design the deployment, infrastructure, CI/CD, model lifecycle controls, monitoring, and rollback mechanisms required to operate the system in production.

## Assumptions

1. The target platform uses FastAPI microservices, event-driven processing, VietOCR-based OCR workers, PostgreSQL, S3-compatible storage, OpenSearch, Redis and or Kafka, Temporal, and a React or Next.js operations UI.
2. The system handles sensitive banking documents and must support strict auditability, controlled releases, and rapid rollback.
3. Models, prompts, thresholds, and rules are all production-managed artifacts and must follow release discipline.
4. Human review and compliance workflows remain business-critical even when the AI stack is degraded.
5. MVP must stay operationally simple, but basic resilience, observability, and rollback cannot be deferred.

## Deliverables

- Environment strategy
- Deployment architecture
- CI/CD workflow
- Model release workflow
- Rollback strategy
- Monitoring metrics
- Alerting thresholds
- Operational dashboards
- Drift and degradation monitoring
- Incident response expectations
- MVP operational setup
- Scale-stage operational evolution

## Dependencies

1. [solution-architecture-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\solution-architecture-blueprint.md)
2. [ai-architecture.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ai-architecture.md)
3. [ml-engineering-plan.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ml-engineering-plan.md)
4. [data-engineering-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\data-engineering-blueprint.md)
5. [backend-engineering-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\backend-engineering-blueprint.md)
6. [security-architecture-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\security-architecture-controls.md)
7. [qa-engineering-test-strategy.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\qa-engineering-test-strategy.md)
8. [prompt-system.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\prompt-system.md)

## Risks

1. Release complexity creates inconsistent service, schema, and workflow versions across environments.
2. Model or threshold changes alter operational outcomes without obvious application code changes.
3. Missing dependency visibility hides storage, queue, workflow, or external compliance degradation until queues back up.
4. Weak rollback discipline causes partial recovery and inconsistent decision behavior.
5. Poor environment parity leads to false confidence from staging validation.

## MVP vs Scale Notes

### MVP

1. Use one primary production region, one staging environment, and one isolated development environment.
2. Keep service count pragmatic:
   API gateway, FastAPI app services, Temporal, one message backbone, PostgreSQL, object storage, OCR workers, OpenSearch, monitoring stack.
3. Use blue-green or rolling deployment for services and shadow or canary release for models.
4. Keep prompt, threshold, and rule releases under the same governance discipline as models.

### Scale

1. Add multi-region failover, warm standby DR, environment-specific model serving pools, and workload isolation by line of business or geography.
2. Add automated drift-triggered retraining pipelines, traffic-splitting model canaries, and policy-as-code controls over production changes.
3. Expand incident automation, autoscaling policies, and forecast-based capacity planning.

## 1. Environment Strategy

### Environment Set

1. Local development
   Used for feature work, unit tests, basic integration tests, and deterministic fixture runs.
2. Shared development
   Used for cross-team integration, early service compatibility checks, and UI/API iteration.
3. Staging
   Production-like environment for release candidates, UAT, benchmark reruns, security validation, and rollback rehearsal.
4. Production
   Live banking operations environment with strict change control, audit logging, and restricted access.
5. Optional DR environment
   Warm standby for disaster recovery exercises and failover validation.

### Environment Rules

1. Each environment must have isolated storage, queues, databases, credentials, and model registries or namespaces.
2. Production data must never be copied into lower environments without approved sanitization and de-identification.
3. Staging must mirror production in deployment topology, configuration shape, monitoring, and key dependency versions.
4. Model and prompt registries must keep environment-specific promotion states:
   `candidate`, `staging_approved`, `production_active`, `production_retired`.
5. Config drift between staging and production is a tracked risk and must be measured.

## 2. Deployment Architecture

### Runtime Topology

```text
Users / Upstream Systems
        |
        v
  WAF / Load Balancer
        |
        v
  API Gateway (Kong / Nginx)
        |
        +------------------------------+
        |                              |
        v                              v
 FastAPI Control Plane            Next.js Review UI
 - case service                   - ops workstation
 - review service                 - audit views
 - integration service            - queue dashboards
 - auth adapters
        |
        +------------------------------+
        |                              |
        v                              v
  Temporal Cluster                 Kafka or Redis/Celery
  - workflow state                 - async jobs
  - retries                        - OCR and extraction tasks
  - timers                         - notification jobs
        |
        +----------------------------------------------------------+
        |                    |                 |                    |
        v                    v                 v                    v
 OCR / AI Workers       Validation svc   Compliance svc      Decision svc
 - OpenCV               - rules engine   - screening adapters - routing gates
 - VietOCR              - schema checks  - policy checks
 - ML scoring
        |
        +----------------------+------------------------+
                               |                        |
                               v                        v
                     PostgreSQL System of Record     S3 / MinIO Evidence Store
                     - cases                         - raw documents
                     - review tasks                  - OCR artifacts
                     - extracted fields              - rendered previews
                     - validations                   - model outputs
                     - decisions                     - audit exports
                               |
                               v
                       OpenSearch / Elasticsearch
                       - case search
                       - operational read models
                               |
                               v
                      Observability Plane
                      - Prometheus / Grafana
                      - ELK / OpenSearch logs
                      - OpenTelemetry tracing
                      - alert manager / on-call
```

### Deployment Principles

1. Control plane and worker plane must be independently deployable.
2. Workflow engine, queue backbone, PostgreSQL, and object storage are tier-0 dependencies and require the strongest availability controls.
3. OCR and ML workers must support GPU and CPU pools, with explicit routing by workload type.
4. OpenSearch is a derived read model and must never become the only source of operational truth.
5. Degraded AI services must not take down case visibility, review, or audit retrieval.

## 3. CI/CD Workflow

### Source Control and Build Flow

1. Pull request flow
   Every service, workflow, prompt, rule, or model manifest change enters through pull request with mandatory checks.
2. Build phase
   Build immutable container images for services and workers with pinned dependencies and signed artifacts.
3. Test phase
   Run unit, contract, integration, security, and regression suites relevant to the changed components.
4. Package phase
   Publish versioned service images, workflow bundles, rule packages, prompt packages, and model manifests.
5. Deploy phase
   Promote to shared development automatically, to staging after required checks, and to production only with approved release gate.

### CI Pipelines

1. Application pipeline
   Lint, type-check, unit tests, API contract tests, integration tests, container build, vulnerability scan, artifact signing.
2. Workflow pipeline
   Validate Temporal workflow definitions, activity contracts, retry policies, and replay compatibility.
3. Data contract pipeline
   Validate schema evolution for events, database migrations, and storage manifests.
4. Prompt pipeline
   Run schema validation, prompt regression suite, safety-case evaluation, and explainability checks.
5. Model pipeline
   Validate training artifacts, evaluation metrics, benchmark deltas, model card completeness, and deployment manifest integrity.
6. Infrastructure pipeline
   Run infrastructure-as-code validation, policy checks, security scans, and plan diff review.

### CD Controls

1. Production deployments require:
   approved change record, successful staging validation, rollback plan, and named owner on point during rollout.
2. Database migrations must be backward compatible for at least one release window where feasible.
3. Service deployment and model deployment must be separately controllable.
4. Changes to thresholds, prompts, and rules must be deployable without rebuilding unrelated services, but still require audit and approval.

## 4. Model Release Workflow

### Managed AI Artifacts

1. VietOCR model package
2. Document classifier model
3. Extraction support models
4. Confidence and anomaly models
5. Prompt bundles
6. Embedding model versions
7. Threshold and routing configuration packages
8. Rule catalog versions

### Release Stages

1. Offline candidate validation
   Evaluate on golden, messy, safety, and slice-specific benchmark sets.
2. Staging deployment
   Run shadow inference and compare against current production-approved baseline.
3. Controlled production canary
   Route a limited fraction of eligible traffic or run shadow-only mode.
4. Production activation
   Promote only after quantitative and operational review sign-off.
5. Post-release observation window
   Track drift, latency, review rate change, disagreement spikes, and exception distribution.

### Rollback Rules

1. Every production model release must have a known previous good version and one-step rollback command or pipeline action.
2. Prompt and threshold rollbacks must be independent from service rollbacks.
3. If a new model increases false auto-pass on safety pack, production rollout stops immediately.
4. If a new model materially changes manual review rate, extraction failure rate, or decision distribution beyond approved bounds, rollback or switch to shadow mode.
5. When rollback occurs, cases already processed by the affected version must be identifiable for targeted review.

### Model Registry Expectations

Each registered artifact must include:

1. version id
2. artifact checksum
3. training data snapshot or dataset manifest
4. feature and label schema version
5. benchmark summary by slice
6. approval status
7. deployment status by environment
8. rollback target version
9. owner
10. release notes

## 5. Rollback Strategy

### Service Rollback

1. Keep at least one previously validated service image ready for re-deploy.
2. Use blue-green or rolling deployment with rapid revert capability.
3. Maintain backward-compatible API and event contracts during rollout window.

### Data Rollback

1. Favor forward-fix for transactional data.
2. Treat destructive schema rollback as exceptional and governed.
3. Backup and restore procedures must be rehearsed on staging and DR environments.
4. Evidence artifacts in object storage must be versioned or write-once where policy requires.

### Workflow Rollback

1. New workflow definitions must preserve replay safety.
2. Running workflows must be identifiable by definition version.
3. If workflow code breaks replay or activity compatibility, halt rollout and revert immediately.

### Model and Prompt Rollback

1. Use traffic split or config-based version pointers, not container rebuilds, for urgent rollback.
2. Keep previous prompt bundle and threshold set active-ready in production control plane.
3. After rollback, generate impacted-case list for retrospective review if required.

## 6. Monitoring Metrics

### Application and Platform Metrics

1. API latency, error rate, throughput, and saturation
2. Queue depth, consumer lag, retry counts, and DLQ counts
3. Temporal workflow success rate, stuck workflows, timeout rates, and activity retries
4. Database latency, connection pool usage, lock contention, replication lag, and storage growth
5. Object storage upload failures, retrieval latency, and integrity check failures
6. OpenSearch indexing lag, query latency, and shard health

### AI and Model Metrics

1. OCR confidence distribution by document type and source channel
2. Classification confidence and confusion by class
3. Extraction completeness for required fields
4. Validation failure rates by rule id and document type
5. Human review rate, rework rate, and reviewer override rate
6. Model disagreement rate between current and shadow candidate
7. Data drift and concept drift indicators by issuer, template, image quality, and channel
8. Model latency and GPU utilization

### Business and Control Metrics

1. Straight-through processing rate
2. Turnaround time by queue and case type
3. Exception rate by reason code
4. Compliance pending backlog
5. Escalation volume by specialist queue
6. Audit write failure count
7. Unauthorized access attempts and denied actions

## 7. Alerting Thresholds

### P1 Immediate Alerts

1. Production outage of API gateway, PostgreSQL, object storage, queue backbone, or Temporal.
2. OCR or extraction worker fleet unavailable beyond threshold.
3. Audit logging failure or evidence write failure.
4. Sudden spike in false auto-pass indicators, high-risk auto-decision attempts, or compliance bypass signals.
5. Large increase in DLQ count or stuck workflows.
6. Unauthorized privileged action attempts above threshold or secrets exposure signal.

### P2 Operational Alerts

1. Rising queue lag or workflow timeout trend.
2. Review backlog breaching SLA.
3. OpenSearch indexing lag affecting case search.
4. Elevated external dependency failure from sanctions, AML, or integration adapters.
5. Material shift in review rate, extraction completeness, or OCR confidence.

### Alert Design Rules

1. Every alert must map to an owner and runbook.
2. Alerts must be grouped by impact:
   availability, data integrity, security, model quality, compliance, and operations SLA.
3. Thresholds must be tuned using staging and early production baselines, then reviewed periodically.
4. Page only on actionable incidents; send lower-severity degradations to Slack, email, or ticketing queues.

### Initial MVP Thresholds

| Signal | Initial Threshold | Expected Response |
| --- | --- | --- |
| API 5xx rate | `> 5%` for 5 minutes | page backend on-call and halt active rollout |
| Workflow stuck count | `> 20` stuck workflows for 10 minutes | investigate Temporal workers and queue health |
| Queue lag | `> 15 minutes` on OCR or extraction queues for 10 minutes | page platform on-call and assess scaling or dependency failure |
| DLQ volume | `> 25` messages in 15 minutes | open incident and stop related new automation if systemic |
| Audit write failure | any sustained failure for 2 minutes | page immediately; treat as release-blocking condition |
| Evidence write failure | `> 3` failures in 10 minutes | page immediately and block affected workflow path |
| OCR worker availability | `< 50%` healthy workers for 5 minutes | page MLOps/platform and shift to review-heavy mode if needed |
| Review backlog SLA breach | `> 10%` of review tasks past SLA for 30 minutes | notify ops lead and product owner |
| External screening adapter failure | `> 20%` failures for 15 minutes | route checks to pending/review-required and notify compliance ops |
| Reviewer override spike | `> 2x` 7-day baseline for 60 minutes | trigger model/prompt degradation investigation |
| OCR confidence shift | median drop `> 15%` vs 7-day baseline for a document class | investigate document quality, model, or preprocessing regression |
| Unauthorized privileged action attempts | `> 5` in 15 minutes from same actor or source | page security and temporarily constrain affected account or origin |

## 8. Operational Dashboards

### Executive Reliability Dashboard

1. platform availability
2. case throughput
3. turnaround time
4. review rate
5. open incidents
6. release health status

### Operations Dashboard

1. queue depth by case type
2. aging by queue
3. case state distribution
4. escalations pending
5. external check backlog
6. document failure reasons

### Engineering Dashboard

1. service latency and error rate
2. workflow retry and timeout heatmap
3. dependency health matrix
4. database and storage performance
5. deployment change timeline

### MLOps Dashboard

1. OCR confidence histograms
2. extraction completeness by field
3. model version traffic split
4. drift indicators
5. shadow-vs-active disagreement rate
6. reviewer override rate by model version

### Security and Control Dashboard

1. privileged access events
2. failed auth and authz attempts
3. secrets rotation status
4. audit write success rate
5. immutable log ingestion status
6. anomaly events affecting sensitive data handling

## 9. Drift and Degradation Monitoring

### Drift Signals

1. OCR confidence distribution shift by document type, issuer, channel, and image-quality bucket.
2. Classification distribution drift and confusion drift by document class.
3. Required-field extraction completeness drift by document type and issuer.
4. Reviewer override rate drift by field, model version, prompt version, and document class.
5. Decision distribution drift:
   auto-pass, manual review, escalate, fail.
6. External dependency degradation impact:
   pending-check backlog, timeout rate, and fallback mode activation rate.

### Degradation Actions

1. Move candidate model from active to shadow-only if disagreement or override rate exceeds approved bounds.
2. Tighten automation thresholds or force review-only mode for affected document classes during active investigation.
3. Roll back prompt bundle or threshold pack independently when degradation is isolated from model weights.
4. Create impacted-case cohort for re-review when degraded versions processed regulated decisions.

### Drift Review Cadence

1. Daily operational review of core quality signals in MVP.
2. Weekly slice review by issuer, channel, document class, and queue.
3. Formal release review before promoting any model, prompt, or threshold change to production.

## 10. Incident Response Expectations

### Support Model

1. DevOps owns platform availability, deployment pipelines, infra health, and rollback execution.
2. MLOps owns model serving health, benchmark regressions, drift triage, and model rollback.
3. Backend owns service defects, workflow correctness, and integration failures.
4. Data engineering owns lineage gaps, dataset pipeline failures, and data-quality incidents.
5. Security owns secrets exposure, access anomalies, and log integrity incidents.
6. Product and operations own business impact assessment and queue-level operational mitigation.

### Incident Expectations

1. Every sev-1 or sev-2 incident must produce:
   timeline, affected components, affected case scope, mitigation, rollback status, and follow-up actions.
2. Incidents affecting decisions or compliance require impacted-case identification and replay or review plan.
3. On-call rotation must have access to dashboards, logs, traces, release history, and rollback procedures.
4. Runbooks must exist for:
   queue backlog, workflow timeout storm, OCR fleet failure, database degradation, object storage outage, model regression, prompt regression, and external screening dependency outage.

## 11. MVP Operational Setup

1. Environments:
   local, shared development, staging, and one production region.
2. Core runtime:
   API gateway, FastAPI services, Temporal, one queue backbone, PostgreSQL, S3/MinIO, OCR/AI workers, OpenSearch, Prometheus, Grafana, centralized logs, and OpenTelemetry.
3. Release controls:
   PR checks, signed container builds, staging validation, manual production approval, and named release owner.
4. Model controls:
   versioned registry or controlled artifact repository, offline benchmark before release, staging shadow validation, and one-step rollback target.
5. On-call setup:
   shared engineering rotation with clear escalation to backend, MLOps, security, and ops leads.
6. Operational mode during AI degradation:
   maintain case intake, review UI, audit visibility, and review-only routing even if automation components are impaired.

## 12. Scale-Stage Operational Evolution

1. Add multi-region failover and tested DR promotion.
2. Split platform, backend, and MLOps on-call rotations with stronger service ownership.
3. Introduce canary traffic splitting by document class or channel for model releases.
4. Add automated drift-triggered investigation and retraining workflows.
5. Expand capacity management with GPU pool autoscaling and queue-aware worker scaling.
6. Add formal SLOs for workflow completion, review latency, and model-service availability by business line.

## Release Governance

### Production Release Gate

1. All mandatory CI checks green.
2. Staging validation complete, including QA regression and security checks.
3. Approved model and prompt artifacts linked to the release record.
4. Rollback path rehearsed and documented.
5. Monitoring and alerts confirmed before traffic shift.
6. Named owner present for release and observation window.

### Post-Release Verification

1. Confirm deployment version inventory across services and workers.
2. Confirm workflow success, queue lag, and database health remain within threshold.
3. Confirm audit writes, evidence writes, and case search indexing continue normally.
4. Compare review rate, exception rate, and confidence distributions against baseline.

## Operational Policy Recommendations

1. Use infrastructure as code for all deployable environments.
2. Treat configuration as versioned code, including thresholds and feature flags.
3. Keep model, prompt, and rule release cadence slower than application release cadence unless emergency fix is required.
4. Never enable wider automation and a new model version in the same release without isolated evaluation.
5. Store release metadata centrally:
   service versions, migration versions, prompt bundle, model bundle, threshold pack, and rule pack.

## Minimum MVP Tooling Baseline

1. Container registry with immutable tags
2. CI pipeline with test, scan, and signed-build stages
3. CD pipeline with staged promotion
4. Prometheus and Grafana
5. Centralized logs with trace correlation ids
6. OpenTelemetry instrumentation
7. Model registry or equivalent controlled artifact repository
8. Runbook repository and incident ownership matrix

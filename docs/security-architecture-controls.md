# Security Architecture and Controls for Ops Agent

## Role

Security Engineer for a banking-grade Document Processing Agent.

## Objective

Define the security architecture, threat model, access controls, encryption requirements, and secure handling policies required for banking documents and related system workflows.

## Assumptions

1. The system handles highly sensitive identity, financial, and operational data.
2. The platform is an internal banking operations system, but internal access is still treated as untrusted by default.
3. Raw documents, OCR artifacts, extracted fields, prompts, and audit records all contain sensitive data and must be protected accordingly.
4. Basic security controls must exist in MVP; they are not deferred to scale.
5. Zero-trust and least-privilege principles apply to both user access and service-to-service access.

## Deliverables

- Threat model
- Security principles
- Access control
- Secure upload handling
- Data storage protection
- Encryption requirements
- Service-to-service security requirements
- Secrets handling
- Logging and audit protection
- Incident considerations
- MVP security baseline
- Scale-stage hardening roadmap
- Security review checklist

## Dependencies

1. [solution-architecture-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\solution-architecture-blueprint.md)
2. [backend-engineering-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\backend-engineering-blueprint.md)
3. [data-engineering-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\data-engineering-blueprint.md)
4. [compliance-risk-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\compliance-risk-controls.md)
5. [frontend-ops-dashboard-blueprint.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\frontend-ops-dashboard-blueprint.md)

## Risks

1. identity and financial data leakage through over-broad access
2. malicious or weaponized file upload
3. secrets sprawl across services and CI/CD
4. compromised service account laterally accessing data stores
5. sensitive data exposure in logs, traces, or prompt artifacts
6. silent tampering with audit records or derived evidence

## MVP vs Scale notes

### MVP

1. enforce RBAC, encryption, upload controls, secret management, and immutable audit logging from day one
2. keep trust boundaries explicit even if deployment topology is simple
3. protect prompts, OCR artifacts, and evidence bundles as sensitive records

### Scale

1. add stronger network segmentation, service mesh identity, HSM-backed key controls, and cross-region key separation
2. mature into adaptive access and device posture checks where justified
3. add continuous control validation and automated policy drift detection

## 1. Threat Model

## 1.1 Protected assets

The following are high-value assets:

1. raw customer identity and financial documents
2. extracted identity, address, and income fields
3. compliance control results and escalation notes
4. prompts, model outputs, and evidence bundles
5. audit logs and lineage records
6. service credentials, encryption keys, and signing keys

## 1.2 Trust boundaries

| Boundary | Description |
|---|---|
| user to gateway | browser/client to public ingress |
| gateway to backend | authenticated service boundary |
| service to service | internal API and event traffic |
| service to storage | database, object store, search, vector store |
| reviewer UI to artifacts | signed or proxied access to sensitive files |
| CI/CD to runtime | deployment and secret injection boundary |

## 1.3 Attack surfaces

1. file upload endpoints
2. public and internal REST APIs
3. Kafka brokers and async job payloads
4. object storage buckets and signed URLs
5. PostgreSQL, OpenSearch, and Weaviate access paths
6. prompt/response artifact storage
7. reviewer UI actions and browser sessions
8. admin/configuration endpoints
9. CI/CD pipelines and secret stores

## 1.4 Threat scenarios and mitigations

| Threat | Likely path | Impact | Core mitigations |
|---|---|---|---|
| malicious file upload | disguised executable, parser exploit, oversized file | remote code execution, malware persistence, storage abuse | allowlist mime/extensions, magic-byte validation, AV/CDR scanning, size limits, quarantine, storage outside webroot |
| stolen user token | phishing, session theft, device compromise | unauthorized case access | short-lived tokens, MFA, secure cookies, token audience checks, re-auth for sensitive actions |
| over-privileged service account | lateral movement after service compromise | broad data exfiltration | per-service IAM, scoped DB roles, scoped bucket prefixes, deny-by-default policies |
| prompt/log artifact exposure | logs or artifacts contain PII/secrets | regulatory breach | encrypt artifacts, redact logs, role-scoped access, avoid logging secrets and full sensitive payloads in central logs |
| audit tampering | direct DB write, admin misuse | loss of accountability | append-only audit model, immutable storage copy, restricted write path, integrity checks |
| insecure internal API | trust-on-network assumption | privilege escalation | mTLS or authenticated service identity, token validation, explicit authorization, zero-trust network posture |
| bucket misconfiguration | public or cross-service exposure | bulk data breach | private buckets, bucket policies, prefix scoping, signed URL proxy, access logging |
| supply chain / CI secret leak | hardcoded secrets or pipeline logs | broad compromise | central secret manager, ephemeral credentials, rotation, CI log masking, signed builds |
| denial of service | upload flood, oversized OCR jobs, log flood | operational outage | rate limiting, quotas, job concurrency limits, back-pressure, log volume controls |

## 2. Security Principles

1. Zero trust by default
   Internal networks, services, and users are not trusted automatically.
2. Least privilege everywhere
   Users and services receive only the minimum permissions needed for their role.
3. Sensitive artifacts are first-class protected assets
   Raw documents, OCR artifacts, extracted fields, prompts, review bundles, and audit records all require strong protection.
4. Prevention plus detection
   Critical controls must include both a preventive mechanism and a way to detect bypass, misuse, or failure.
5. Fail closed on high-risk ambiguity
   When security, fraud, or compliance state is uncertain, the system should block unsafe progression and require review.
6. Immutable accountability
   Material user and system actions must be reconstructable later without relying on mutable operational tables.

## 3. Security Control Matrix

| Control ID | Area | Requirement | Default posture | Owner |
|---|---|---|---|---|
| SEC-01 | Authentication | All user access must authenticate through Keycloak with MFA for privileged roles | mandatory | Security + Platform |
| SEC-02 | Authorization | RBAC with least privilege per role and queue | deny by default | Security + Backend |
| SEC-03 | Service identity | Every service must use a distinct machine identity / credential | mandatory | Platform |
| SEC-04 | Upload security | Uploaded files must pass extension, mime, signature, and malware controls before workflow entry | mandatory | Backend + Security |
| SEC-05 | Storage isolation | Raw and derived artifacts must remain in private object storage, never public buckets | mandatory | Data Platform |
| SEC-06 | Encryption at rest | Sensitive stores must use strong encryption with managed keys | mandatory | Platform + Security |
| SEC-07 | Encryption in transit | TLS for all external traffic; authenticated encrypted internal traffic | mandatory | Platform |
| SEC-08 | Secret management | No plaintext secrets in code, config, logs, or images | mandatory | Security + DevOps |
| SEC-09 | Audit protection | Audit events must be append-only and protected from tampering | mandatory | Platform + Audit |
| SEC-10 | Log protection | Sensitive data must be masked or excluded from central logs | mandatory | SRE + Security |
| SEC-11 | Admin separation | No self-approval of material security/model/prompt changes | mandatory | Risk + Engineering |
| SEC-12 | Access review | Periodic review of user and service access | mandatory | Security |
| SEC-13 | Data retention control | Purge must respect legal hold and retention class | mandatory | Compliance + Records |
| SEC-14 | Incident visibility | Security-relevant failures and access anomalies must alert | mandatory | SRE + Security |
| SEC-15 | Dependency hardening | Image, library, and build pipeline scanning required | mandatory | Platform + Engineering |

## 4. Access Control Model

## 4.1 User access model

Use Keycloak-backed RBAC with explicit role-to-permission mapping.

### Roles

1. branch_support
2. operations_reviewer
3. compliance_analyst
4. fraud_analyst
5. back_office
6. supervisor
7. platform_admin
8. security_admin

### Permission principles

1. no wildcard read access to all artifacts
2. queue-scoped and role-scoped access by default
3. approval, rejection, escalation, and export actions require explicit permission
4. restricted fraud and compliance notes remain segregated

## 4.2 Service-to-data authorization

### PostgreSQL

1. separate DB roles per service
2. no service gets blanket write access across all schemas
3. audit tables writable only through audit-service path

### S3 / MinIO

1. per-service bucket prefix policies
2. write/read separation where feasible
3. no direct browser bucket credentials

### OpenSearch / Weaviate

1. read/write credentials scoped to owning service
2. UI accesses search through backend APIs, not direct cluster exposure

## 4.3 Step-up authentication

Require stronger user verification for:

1. exporting audit bundles
2. changing user roles
3. approving sensitive escalated cases if policy requires
4. admin configuration of routing, prompt, or model versions

## 5. Secure Upload Handling Requirements

## 5.1 Upload policy

For every uploaded file:

1. require authenticated user and authorized workflow
2. validate allowlisted extension
3. validate MIME type
4. validate file signature / magic bytes
5. rename server-side to generated object key
6. enforce size and page-count limits
7. scan with antivirus
8. apply CDR / content-disarm policy where appropriate for high-risk file types
9. quarantine suspicious or unreadable files

Do not trust:

1. user-provided filename
2. user-provided content type
3. client-side validation alone

## 5.2 Upload outcomes

Every upload must end in one of these explicit states before workflow continuation:

1. `accepted`
2. `rejected`
3. `quarantined`
4. `manual_resubmission_required`

No upload may silently continue into normal processing without one of these recorded outcomes.

## 5.3 Quarantine behavior

Quarantined files:

1. do not enter normal workflow processing
2. are tagged with reason and trace ID
3. are visible only to authorized operations/security roles
4. create an audit event and review item

## 6. Data Storage Protection Requirements

## 6.1 Storage policy

1. store files outside the webroot and behind authenticated application access
2. raw files are immutable
3. derived artifacts are versioned
4. bucket/object access is logged
5. signed URLs are short-lived and audience-scoped
6. sensitive prompts and AI artifacts use the same protection class as source evidence unless stricter policy applies
7. PostgreSQL remains the source of truth for workflow, review, and audit metadata; OpenSearch remains a projection only
8. no public bucket, anonymous object access, or direct browser storage credentials

## 6.2 Data classification expectations

Treat these as confidential-regulated by default:

1. raw customer identity and financial documents
2. extracted identity, address, and income values
3. OCR and layout artifacts
4. prompts and model responses
5. review bundles and specialist notes
6. audit and lineage records containing operator or customer context

## 7. Encryption Requirements

## 7.1 At-rest encryption

1. use strong encryption for object storage, database volumes, backups, and search volumes
2. prefer centrally managed KMS-backed keys
3. for cryptographic modules and key handling, prefer FIPS 140-3 validated components where required by bank policy
4. separate keys or key policies by environment and, at scale, by region / data domain

## 7.2 In-transit encryption

1. TLS 1.2+ minimum, prefer TLS 1.3 where supported
2. external ingress must terminate only at approved gateway/load balancer
3. internal service traffic should be encrypted and authenticated; at scale, use mTLS or service-mesh identity
4. database and broker connections must use TLS where supported

## 7.3 Key management requirements

1. keys must be centrally inventoried
2. key access must be role-scoped and auditable
3. rotate keys according to policy and incident triggers
4. backup and recovery procedures must protect key material separately
5. key metadata is sensitive and must be protected as well

## 8. Service-to-Service Security Requirements

## 8.1 Internal API security

1. every internal API call must authenticate the caller service
2. every internal API must authorize by service role, not by network location alone
3. internal APIs must validate input schemas strictly
4. all internal mutating actions must emit auditable events

## 8.2 Event and queue security

1. Kafka and job infrastructure must require authenticated producers and consumers
2. topics and queues must use ACLs per service role
3. sensitive payloads should carry references to artifacts rather than full sensitive bodies where practical
4. failed messages must not leak sensitive payloads into insecure logs or alerts

## 8.3 Network expectations

1. default-deny network rules between services
2. only required service-to-service paths opened
3. admin interfaces and backing stores are not internet exposed

## 9. Secrets Management Requirements

## 9.1 Secret management rules

1. no secrets in source code, container images, or static config files
2. secrets must come from a centralized secret manager or equivalent controlled mechanism
3. use short-lived, scoped credentials where possible
4. rotate secrets regularly and on suspicion of compromise
5. CI/CD logs must mask secrets and avoid echoing them

## 9.2 Secret classes

| Secret type | Handling rule |
|---|---|
| database credentials | per-service credential, rotated, not shared |
| object storage credentials | scoped to bucket/prefix and operation type |
| JWT signing / OIDC secrets | tightly restricted, rotation planned, audit access |
| API keys for external services | service-scoped, least privilege, usage monitored |
| TLS private keys | protected in KMS/HSM-backed path where feasible |
| encryption keys | managed under key-management policy, not application-owned flat files |

## 9.3 Runtime secret delivery

1. deliver secrets at runtime, not build time
2. prefer environment injection from a managed secret source or mounted ephemeral secret volume
3. avoid long-lived secret material in local disk where possible

## 10. Logging and Audit Protection Requirements

## 10.1 What to log

Log:

1. authentication events
2. authorization denials
3. case creation and mutation events
4. upload acceptance/rejection/quarantine
5. review, escalation, and close actions
6. secret access and admin changes
7. model/prompt/rule version changes

## 10.2 What not to log directly

Do not log directly into central logs:

1. raw document content
2. full OCR text for sensitive documents unless routed to protected evidence storage
3. access tokens
4. passwords
5. database connection strings
6. encryption keys or primary secrets
7. unrestricted PII payload dumps

Instead:

1. store full sensitive artifacts in encrypted evidence storage
2. log references, hashes, and trace IDs centrally

## 10.3 Log protection

1. logs must be integrity-protected and access-controlled
2. log shipping channels must be encrypted
3. log retention and disposal must follow policy
4. log flood controls must exist to protect availability
5. audit logs and security logs should be harder to alter than standard app logs

## 11. Incident Considerations

## 11.1 Incident classes

1. suspected data exposure
2. compromised user session or privileged account misuse
3. compromised service credential
4. malware or weaponized upload event
5. audit integrity failure
6. storage or key-management misconfiguration

## 11.2 Incident response expectations

1. every security-relevant incident must have a severity, owner, and traceable response record
2. affected cases, documents, services, users, and secrets must be identifiable quickly
3. compromised secrets must be revocable and rotatable without code changes
4. suspicious uploads must remain quarantined and blocked from normal workflow processing
5. incidents affecting decision integrity or evidence integrity must trigger impacted-case review and, where needed, manual re-review

## 11.3 Detection expectations

1. alert on repeated authentication failures and abnormal privilege use
2. alert on malware detections, quarantine spikes, or suspicious upload patterns
3. alert on audit-write failures or audit integrity-check failures
4. alert on unusual service-to-service access patterns or bucket policy changes

## 12. MVP Security Baseline

1. Keycloak-backed authentication with MFA for privileged roles
2. RBAC and deny-by-default authorization
3. authenticated gateway and service APIs
4. private object storage with short-lived signed access
5. encryption at rest and in transit
6. malware scanning, MIME validation, and quarantine path for uploads
7. append-only audit event path
8. centralized secret management
9. structured logging with sensitive-data exclusion or redaction
10. baseline image and dependency scanning in CI/CD

## 13. Scale-Stage Hardening Roadmap

### 13.1 Near-scale hardening

1. mTLS or workload identity for service-to-service traffic
2. stronger network segmentation and policy enforcement
3. environment and region-specific key separation
4. automated access review and policy drift detection

### 13.2 Later-stage hardening

1. HSM-backed key management where required
2. adaptive access and device posture checks for privileged users
3. stronger audit integrity verification and tamper detection
4. automated control validation and configuration compliance scanning

## 14. Security Review Checklist

Use this checklist before pilot or production release.

### Access control

1. Are all user roles defined with least privilege?
2. Are restricted compliance/fraud actions hidden and blocked server-side?
3. Are service accounts scoped per service and per store?

### Upload and file handling

1. Are extension, MIME, and file-signature validation enforced?
2. Are file size and page count limits enforced?
3. Is AV or equivalent scanning active?
4. Are quarantined files isolated from normal processing?

### Storage and encryption

1. Are raw and derived artifacts private by default?
2. Are object, DB, and backup stores encrypted at rest?
3. Are all service and user paths encrypted in transit?
4. Are key-management responsibilities defined?

### Secrets

1. Are secrets absent from code, images, and static configs?
2. Are secret rotation and revocation procedures documented?
3. Are CI/CD logs and pipelines hardened against secret leakage?

### Logging and audit

1. Are security-relevant events logged?
2. Are sensitive values masked or excluded from logs?
3. Are audit records append-only and integrity-protected?
4. Are log access rights restricted and reviewed?

### Service and network security

1. Are internal APIs authenticated and authorized?
2. Are broker/topic ACLs configured?
3. Is network access default-deny?
4. Are data stores and admin endpoints non-public?

### Application security

1. Are input schemas strictly validated?
2. Are error responses sanitized?
3. Are retries bounded and visible?
4. Are signed URLs short-lived and access-scoped?

### Governance

1. Are model/prompt/rule changes approval-gated?
2. Are privileged access reviews scheduled?
3. Are incident response paths defined for file malware, data leak, and credential compromise?

## 15. Recommended Security Stance

Ops Agent should assume:

1. every user is role-limited,
2. every service can be compromised,
3. every file can be hostile,
4. every artifact may be audited later.

That produces the correct default posture for a banking document platform.

## 16. Source Notes

This document was written using primary guidance current as checked on April 14, 2026. Useful anchors:

1. Zero trust architecture: [NIST SP 800-207](https://www.nist.gov/publications/zero-trust-architecture)
2. Current digital identity guidelines: [NIST SP 800-63-4](https://www.nist.gov/publications/nist-sp-800-63-4-digital-identity-guidelines)
3. Identity proofing and enrollment: [NIST SP 800-63A-4](https://www.nist.gov/publications/nist-sp-800-63a-4digital-identity-guidelines-identity-proofing-and-enrollment)
4. Key management guidance: [NIST SP 800-57 Part 1 Rev. 5](https://www.nist.gov/publications/recommendation-key-management-part-1-general-1)
5. FIPS cryptographic modules baseline: [FIPS 140-3](https://www.nist.gov/news-events/news/2019/05/announcing-approval-and-issuance-fips-140-3-security-requirements)
6. Secure file upload practices: [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
7. Secure secrets handling: [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
8. Logging protection guidance: [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

Where this document goes beyond those sources, it does so as a conservative engineering recommendation for a banking environment.

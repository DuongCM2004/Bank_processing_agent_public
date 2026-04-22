import type {
  AuditEvent,
  CaseDetail,
  CaseListResponse,
  CaseSummary,
  ComplianceFinding,
  Decision,
  ExtractionResult,
  ManualReviewAction,
  RiskFinding,
  ValidationFinding,
} from "@/api/contracts";
import type { CaseWorkspaceViewModel } from "@/features/cases/workspace";
import { buildCaseWorkspaceViewModel } from "@/features/cases/workspace";

interface QueryStateOverrides<T> {
  data?: T;
  isLoading?: boolean;
  isError?: boolean;
  refetch?: () => unknown;
}

interface CaseListOverrides {
  items?: CaseSummary[];
  total?: number;
  limit?: number;
  offset?: number;
}

const DEFAULT_REFETCH = () => Promise.resolve(undefined);

export function buildQueryState<T>({
  data,
  isLoading = false,
  isError = false,
  refetch = DEFAULT_REFETCH,
}: QueryStateOverrides<T>) {
  return {
    data,
    isLoading,
    isError,
    refetch,
  };
}

export function buildLoadingQueryState<T>(refetch?: () => unknown) {
  return buildQueryState<T>({
    data: undefined,
    isLoading: true,
    isError: false,
    refetch,
  });
}

export function buildErrorQueryState<T>(refetch?: () => unknown) {
  return buildQueryState<T>({
    data: undefined,
    isLoading: false,
    isError: true,
    refetch,
  });
}

export function buildCaseSummary(overrides: Partial<CaseSummary> = {}): CaseSummary {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    case_reference: "CASE-AAA",
    case_type: "kyc_onboarding",
    status: "manual_review_required",
    status_changed_at: "2026-04-15T10:00:00Z",
    current_queue: "document_ops",
    source_channel: "manual_upload",
    customer_reference: null,
    document_count: 2,
    created_at: "2026-04-15T08:00:00Z",
    updated_at: "2026-04-15T10:30:00Z",
    ...overrides,
  };
}

export function buildCaseListResponse({
  items = [buildCaseSummary()],
  total = items.length,
  limit = 10,
  offset = 0,
}: CaseListOverrides = {}): CaseListResponse {
  return {
    items,
    total,
    limit,
    offset,
  };
}

export function buildValidationFinding(overrides: Partial<ValidationFinding> = {}): ValidationFinding {
  return {
    id: "vf-1",
    case_id: "case-123",
    document_id: "doc-1",
    extraction_result_id: "ext-1",
    rule_code: "document_number_check",
    field_name: "document_number",
    message: "Document number requires confirmation.",
    severity: "warning",
    status: "open",
    resolution_note: null,
    evidence_refs: [],
    created_at: "2026-04-15T09:00:00Z",
    updated_at: "2026-04-15T09:00:00Z",
    ...overrides,
  };
}

export function buildRiskFinding(overrides: Partial<RiskFinding> = {}): RiskFinding {
  return {
    id: "rf-1",
    case_id: "case-123",
    document_id: "doc-1",
    extraction_result_id: "ext-1",
    risk_code: "sanctions_watchlist",
    message: "Potential watchlist similarity detected.",
    risk_level: "high",
    status: "open",
    risk_score: 0.88,
    evidence_refs: [],
    created_at: "2026-04-15T10:00:00Z",
    updated_at: "2026-04-15T10:00:00Z",
    ...overrides,
  };
}

export function buildComplianceFinding(overrides: Partial<ComplianceFinding> = {}): ComplianceFinding {
  return {
    id: "cf-1",
    case_id: "case-123",
    document_id: "doc-1",
    extraction_result_id: "ext-1",
    policy_code: "kyc_document_complete",
    regulation_reference: "KYC-4.2",
    message: "Required documentation set has been completed.",
    severity: "info",
    status: "resolved",
    evidence_refs: [],
    created_at: "2026-04-15T10:00:00Z",
    updated_at: "2026-04-15T10:00:00Z",
    ...overrides,
  };
}

export function buildExtractionResult(overrides: Partial<ExtractionResult> = {}): ExtractionResult {
  return {
    id: "ext-1",
    document_id: "doc-1",
    ocr_result_id: null,
    status: "completed",
    schema_name: "passport_mvp",
    extracted_payload: { document_number: "ABC123" },
    confidence_score: 0.91,
    evidence_refs: [],
    provider_name: "placeholder_extraction",
    provider_job_id: null,
    processed_at: "2026-04-15T09:00:00Z",
    model_version: null,
    created_at: "2026-04-15T09:00:00Z",
    updated_at: "2026-04-15T09:00:00Z",
    ...overrides,
  };
}

export function buildDecision(overrides: Partial<Decision> = {}): Decision {
  return {
    id: "decision-1",
    case_id: "case-123",
    decided_by_user_id: "user-1",
    decision_type: "reviewer_decision",
    outcome: "review_required",
    reason_code: "supervisor_review_required",
    rationale: "Additional review required.",
    confidence_score: 0.72,
    evidence_refs: [],
    linked_findings: [{ finding_type: "validation", finding_id: "vf-1" }],
    supersedes_decision_id: null,
    created_at: "2026-04-15T10:00:00Z",
    updated_at: "2026-04-15T10:00:00Z",
    ...overrides,
  };
}

export function buildManualReviewAction(overrides: Partial<ManualReviewAction> = {}): ManualReviewAction {
  return {
    id: "mra-1",
    case_id: "case-123",
    document_id: "doc-1",
    performed_by_user_id: "user-1",
    related_decision_id: null,
    action_type: "escalate",
    comment: "Escalated for reviewer confirmation.",
    payload: {},
    evidence_refs: [],
    created_at: "2026-04-15T10:00:00Z",
    updated_at: "2026-04-15T10:00:00Z",
    ...overrides,
  };
}

export function buildAuditEvent(overrides: Partial<AuditEvent> = {}): AuditEvent {
  return {
    id: "audit-1",
    case_id: "case-123",
    actor_user_id: "user-1",
    actor_type: "user",
    actor_identifier: "user-1",
    event_type: "manual_review_action_recorded",
    summary: "Manual review action 'escalate' was recorded.",
    resource_type: "manual_review_action",
    resource_id: "mra-1",
    occurred_at: "2026-04-15T10:00:00Z",
    metadata: {},
    evidence_refs: [],
    created_at: "2026-04-15T10:00:00Z",
    updated_at: "2026-04-15T10:00:00Z",
    ...overrides,
  };
}

export function buildCaseDetail(overrides: Partial<CaseDetail> = {}): CaseDetail {
  return {
    id: "case-123",
    case_reference: "CASE-123",
    case_type: "kyc_onboarding",
    status: "manual_review_required",
    status_changed_at: "2026-04-15T10:00:00Z",
    current_queue: "document_ops",
    source_channel: "manual_upload",
    customer_reference: null,
    created_at: "2026-04-15T08:00:00Z",
    updated_at: "2026-04-15T10:30:00Z",
    submitted_by_user: null,
    metadata: {},
    documents: [
      {
        id: "doc-1",
        case_id: "case-123",
        filename: "passport.pdf",
        document_type: "passport",
        mime_type: "application/pdf",
        source_channel: "manual_upload",
        storage_key: "cases/case-123/passport.pdf",
        sha256_digest: "a".repeat(64),
        file_size_bytes: 1024,
        uploaded_at: "2026-04-15T08:00:00Z",
        status: "review_required",
        status_changed_at: "2026-04-15T10:00:00Z",
        page_count: 1,
        metadata: {},
        created_at: "2026-04-15T08:00:00Z",
        updated_at: "2026-04-15T10:00:00Z",
      },
    ],
    ocr_results: [],
    extraction_results: [buildExtractionResult()],
    validation: {
      case_id: "case-123",
      validation_findings: [buildValidationFinding()],
      risk_findings: [],
      compliance_findings: [],
      has_blocking_findings: false,
    },
    decisions: [buildDecision()],
    manual_review_actions: [buildManualReviewAction()],
    audit_events: [buildAuditEvent()],
    closed_at: null,
    ...overrides,
  };
}

export function buildCaseWorkspace(overrides: Partial<CaseDetail> = {}): CaseWorkspaceViewModel {
  return buildCaseWorkspaceViewModel(buildCaseDetail(overrides));
}

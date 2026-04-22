import { apiClient } from "@/api/client";
import type {
  AuditEvent,
  CaseCreateRequest,
  CaseDetail,
  CaseListResponse,
  CaseStatus,
  CaseStatusTransitionRequest,
  CaseStatusTransitionResponse,
  Decision,
  DecisionCreateRequest,
  DocumentUploadMetadata,
  QueueProcessingRequest,
  QueueProcessingResponse,
} from "@/api/contracts";
import { listCaseAuditEvents } from "@/features/audit/api";

interface ListCasesParams {
  limit?: number;
  offset?: number;
  status?: CaseStatus;
  currentQueue?: string;
  caseType?: string;
}

interface BackendCase {
  id: string;
  case_reference: string;
  case_type: string;
  status: CaseStatus;
  status_changed_at: string;
  current_queue: string;
  source_channel: string;
  customer_reference?: string | null;
  case_metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

interface BackendCaseListResponse {
  items: BackendCase[];
  total: number;
  limit: number;
  offset: number;
}

interface BackendDocument {
  id: string;
  case_id: string;
  filename: string;
  document_type: string;
  mime_type: string;
  storage_key: string;
  sha256_digest: string;
  status: DocumentUploadMetadata["status"];
  file_size_bytes: number;
  uploaded_at: string;
  document_metadata: Record<string, unknown>;
}

interface BackendDocumentListResponse {
  items: BackendDocument[];
  total: number;
}

interface BackendDecision {
  id: string;
  case_id: string;
  outcome: Decision["outcome"];
  decided_by: string;
  rationale: string;
  evidence_refs: Decision["evidence_refs"];
  decision_metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

function normalizeRecord(value: Record<string, unknown> | undefined): Record<string, string> {
  return Object.fromEntries(Object.entries(value ?? {}).map(([key, entry]) => [key, typeof entry === "string" ? entry : JSON.stringify(entry)]));
}

function isUuid(value: string) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
}

export function normalizeCaseSummary(item: BackendCase): CaseListResponse["items"][number] {
  return {
    id: item.id,
    case_reference: item.case_reference,
    case_type: item.case_type,
    status: item.status,
    status_changed_at: item.status_changed_at,
    current_queue: item.current_queue,
    source_channel: item.source_channel,
    customer_reference: item.customer_reference,
    document_count: 0,
    created_at: item.created_at,
    updated_at: item.updated_at,
  };
}

function normalizeDocument(item: BackendDocument): DocumentUploadMetadata {
  return {
    id: item.id,
    case_id: item.case_id,
    filename: item.filename,
    document_type: item.document_type,
    mime_type: item.mime_type,
    source_channel: "manual_upload",
    storage_key: item.storage_key,
    sha256_digest: item.sha256_digest,
    file_size_bytes: item.file_size_bytes,
    uploaded_at: item.uploaded_at,
    status: item.status,
    status_changed_at: item.uploaded_at,
    page_count: null,
    metadata: normalizeRecord(item.document_metadata),
    created_at: item.uploaded_at,
    updated_at: item.uploaded_at,
  };
}

export function normalizeDecision(item: BackendDecision): Decision {
  return {
    id: item.id,
    case_id: item.case_id,
    decided_by_user_id: item.decided_by,
    decision_type: "reviewer_decision",
    outcome: item.outcome,
    reason_code: String(item.decision_metadata.reason_code ?? item.outcome),
    rationale: item.rationale,
    confidence_score: typeof item.decision_metadata.confidence_score === "number" ? item.decision_metadata.confidence_score : null,
    evidence_refs: item.evidence_refs,
    linked_findings: [],
    supersedes_decision_id: null,
    created_at: item.created_at,
    updated_at: item.updated_at,
  };
}

function emptyValidation(caseId: string): CaseDetail["validation"] {
  return {
    case_id: caseId,
    validation_findings: [],
    risk_findings: [],
    compliance_findings: [],
    has_blocking_findings: false,
  };
}

function normalizeCaseDetail(
  item: BackendCase,
  documents: DocumentUploadMetadata[],
  auditEvents: AuditEvent[],
): CaseDetail {
  return {
    id: item.id,
    case_reference: item.case_reference,
    case_type: item.case_type,
    status: item.status,
    status_changed_at: item.status_changed_at,
    current_queue: item.current_queue,
    source_channel: item.source_channel,
    customer_reference: item.customer_reference,
    created_at: item.created_at,
    updated_at: item.updated_at,
    submitted_by_user: null,
    metadata: normalizeRecord(item.case_metadata),
    documents,
    ocr_results: [],
    extraction_results: [],
    validation: emptyValidation(item.id),
    decisions: [],
    manual_review_actions: [],
    audit_events: auditEvents,
    closed_at: null,
  };
}

export function listCases(params: ListCasesParams = {}) {
  return apiClient
    .get<BackendCaseListResponse>("/cases", {
      limit: params.limit ?? 20,
      offset: params.offset ?? 0,
      status: params.status,
      current_queue: params.currentQueue,
      case_type: params.caseType,
    })
    .then((response) => ({
      ...response,
      items: response.items.map(normalizeCaseSummary),
    }));
}

export function createCase(request: CaseCreateRequest) {
  return apiClient.post<BackendCase, CaseCreateRequest>("/cases", request).then(normalizeCaseSummary);
}

export function getCase(caseId: string) {
  return apiClient.get<BackendCase>(`/cases/${caseId}`);
}

export function deleteCase(caseId: string) {
  return apiClient.delete(`/cases/${caseId}`);
}

export function transitionCaseStatus(caseId: string, request: CaseStatusTransitionRequest) {
  return apiClient.patch<CaseStatusTransitionResponse, CaseStatusTransitionRequest>(`/cases/${caseId}/status`, request);
}

export function listCaseDocuments(caseId: string) {
  return apiClient
    .get<BackendDocumentListResponse>(`/cases/${caseId}/documents`)
    .then((response) => ({ ...response, items: response.items.map(normalizeDocument) }));
}

export function uploadCaseDocument(
  caseId: string,
  request: {
    file: File;
    documentType: string;
    documentMetadata?: Record<string, unknown>;
    actorId?: string | null;
  },
) {
  const body = new FormData();
  body.set("file", request.file);
  body.set("document_type", request.documentType);
  body.set("metadata", JSON.stringify(request.documentMetadata ?? {}));
  if (request.actorId && isUuid(request.actorId)) {
    body.set("uploaded_by_user_id", request.actorId);
  }

  return apiClient.postForm<BackendDocument>(`/cases/${caseId}/documents`, body).then(normalizeDocument);
}

export function queueCaseProcessing(caseId: string, request: QueueProcessingRequest) {
  return apiClient.post<QueueProcessingResponse, QueueProcessingRequest>(`/cases/${caseId}/processing/queue`, request, {
    timeoutMs: 120_000,
  });
}

export function createDecision(caseId: string, request: DecisionCreateRequest) {
  return apiClient.post<BackendDecision, DecisionCreateRequest>(`/cases/${caseId}/decisions`, request).then(normalizeDecision);
}

export function getCaseDetail(caseId: string) {
  return Promise.all([
    getCase(caseId),
    listCaseDocuments(caseId).then((response) => response.items),
    listCaseAuditEvents({ caseId, limit: 20, offset: 0 }).then((response) => response.items),
  ]).then(([item, documents, auditEvents]) => normalizeCaseDetail(item, documents, auditEvents));
}

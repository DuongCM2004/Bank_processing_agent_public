export type CaseStatus =
  | "created"
  | "documents_uploaded"
  | "queued_for_processing"
  | "processing"
  | "extraction_completed"
  | "validation_completed"
  | "manual_review_required"
  | "decision_ready"
  | "approved"
  | "rejected"
  | "failed";

export type DocumentStatus =
  | "uploaded"
  | "stored"
  | "queued"
  | "preprocessing"
  | "extracting"
  | "validating"
  | "retrying"
  | "extracted"
  | "in_review"
  | "approved"
  | "rejected"
  | "persisted"
  | "ocr_pending"
  | "ocr_completed"
  | "extraction_completed"
  | "review_required"
  | "failed"
  | "archived";

export type ProcessingStatus = "pending" | "in_progress" | "completed" | "failed";
export type FindingSeverity = "info" | "warning" | "error" | "critical";
export type FindingStatus = "open" | "resolved" | "waived";
export type RiskLevel = "low" | "medium" | "high" | "critical";
export type DecisionOutcome = "approved" | "rejected" | "review_required" | "escalated";
export type DecisionType = "system_recommendation" | "reviewer_decision" | "supervisor_decision";
export type ManualReviewActionType =
  | "add_note"
  | "claim"
  | "unclaim"
  | "confirm_extraction"
  | "correct_data"
  | "request_reprocessing"
  | "escalate"
  | "approve"
  | "reject"
  | "close";
export type AuditActorType = "system" | "user" | "service";
export type AuditEventType =
  | "case_created"
  | "document_added"
  | "ocr_completed"
  | "extraction_completed"
  | "validation_completed"
  | "finding_created"
  | "decision_recorded"
  | "manual_review_action_recorded"
  | "status_changed"
  | "processing_queued"
  | "document_queued"
  | "document_review_started"
  | "document_approved"
  | "document_rejected"
  | "document_persisted"
  | "document_failed";

export interface IdentityDocumentExtraction {
  document_type: string | null;
  full_name: string | null;
  first_name: string | null;
  last_name: string | null;
  id_number: string | null;
  document_number: string | null;
  date_of_birth: string | null;
  sex: string | null;
  gender: string | null;
  nationality: string | null;
  place_of_birth: string | null;
  issue_date: string | null;
  expiry_date: string | null;
  issuing_authority: string | null;
  address: string | null;
  raw_full_text: string | null;
}

export interface DocumentStatusResponse {
  document_uuid: string;
  status: DocumentStatus;
  extraction_uuid?: string | null;
  extraction_status?: ProcessingStatus | null;
  updated_at: string;
}

export interface DocumentExtractionField {
  field_name: keyof IdentityDocumentExtraction;
  extracted_value?: string | null;
  reviewed_value?: string | null;
}

export interface DocumentExtractionResponse {
  document_uuid: string;
  extraction_uuid?: string | null;
  status: DocumentStatus;
  fields: DocumentExtractionField[];
  extracted_payload: Record<string, unknown>;
  reviewed_payload?: Record<string, unknown> | null;
  raw_full_text?: string | null;
}

export interface DocumentReviewRequest {
  action: "edit" | "approve" | "reject";
  reviewer_id: string;
  reviewed_payload?: IdentityDocumentExtraction | null;
  comment?: string | null;
}

export interface DocumentReviewResponse {
  document_uuid: string;
  extraction_uuid?: string | null;
  status: DocumentStatus;
  action_id: string;
}

export interface EvidenceReference {
  document_id: string;
  page_number?: number | null;
  text_anchor?: string | null;
  extracted_value?: string | null;
  metadata: Record<string, string>;
}

export interface DocumentUploadMetadata {
  id: string;
  case_id: string;
  filename: string;
  document_type: string;
  mime_type: string;
  source_channel: string;
  storage_key: string;
  sha256_digest: string;
  file_size_bytes?: number | null;
  uploaded_at: string;
  status: DocumentStatus;
  status_changed_at: string;
  page_count?: number | null;
  metadata: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface OCRResult {
  id: string;
  document_id: string;
  status: ProcessingStatus;
  raw_text?: string | null;
  confidence_score?: number | null;
  provider_name: string;
  provider_job_id?: string | null;
  processed_at?: string | null;
  page_count?: number | null;
  result_metadata: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface ExtractionResult {
  id: string;
  document_id: string;
  ocr_result_id?: string | null;
  status: ProcessingStatus;
  schema_name: string;
  extracted_payload: Record<string, unknown>;
  confidence_score?: number | null;
  evidence_refs: EvidenceReference[];
  provider_name: string;
  provider_job_id?: string | null;
  processed_at?: string | null;
  model_version?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ValidationFinding {
  id: string;
  case_id: string;
  document_id?: string | null;
  extraction_result_id?: string | null;
  rule_code: string;
  field_name?: string | null;
  message: string;
  severity: FindingSeverity;
  status: FindingStatus;
  resolution_note?: string | null;
  evidence_refs: EvidenceReference[];
  created_at: string;
  updated_at: string;
}

export interface RiskFinding {
  id: string;
  case_id: string;
  document_id?: string | null;
  extraction_result_id?: string | null;
  risk_code: string;
  message: string;
  risk_level: RiskLevel;
  status: FindingStatus;
  risk_score?: number | null;
  evidence_refs: EvidenceReference[];
  created_at: string;
  updated_at: string;
}

export interface ComplianceFinding {
  id: string;
  case_id: string;
  document_id?: string | null;
  extraction_result_id?: string | null;
  policy_code: string;
  regulation_reference?: string | null;
  message: string;
  severity: FindingSeverity;
  status: FindingStatus;
  evidence_refs: EvidenceReference[];
  created_at: string;
  updated_at: string;
}

export interface ValidationResult {
  case_id: string;
  validation_findings: ValidationFinding[];
  risk_findings: RiskFinding[];
  compliance_findings: ComplianceFinding[];
  has_blocking_findings: boolean;
}

export interface DecisionFindingLink {
  finding_type: string;
  finding_id: string;
}

export interface Decision {
  id: string;
  case_id: string;
  decided_by_user_id?: string | null;
  decision_type: DecisionType;
  outcome: DecisionOutcome;
  reason_code: string;
  rationale?: string | null;
  confidence_score?: number | null;
  evidence_refs: EvidenceReference[];
  linked_findings: DecisionFindingLink[];
  supersedes_decision_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ManualReviewAction {
  id: string;
  case_id: string;
  document_id?: string | null;
  performed_by_user_id: string;
  reviewer_id?: string;
  related_decision_id?: string | null;
  action_type: ManualReviewActionType;
  comment?: string | null;
  payload: Record<string, unknown>;
  evidence_refs: readonly EvidenceReference[];
  created_at: string;
  updated_at: string;
}

export interface ManualReviewNoteRequest {
  performed_by_user_id: string;
  document_id?: string | null;
  comment: string;
  evidence_refs?: EvidenceReference[];
}

export interface ManualReviewCorrectionFieldRequest {
  extraction_result_id: string;
  field_name: string;
  before_value: unknown | null;
  after_value: unknown | null;
  evidence_refs?: EvidenceReference[];
}

export interface ManualCorrectionSubmissionRequest {
  performed_by_user_id: string;
  document_id?: string | null;
  comment?: string | null;
  corrections: ManualReviewCorrectionFieldRequest[];
  evidence_refs?: EvidenceReference[];
}

export interface ManualReviewCorrectionFieldResponse {
  extraction_result_id: string;
  field_name: string;
  before_value: unknown | null;
  after_value: unknown | null;
  evidence_refs: EvidenceReference[];
}

export interface ManualCorrectionSubmissionResponse {
  case_id: string;
  case_status: CaseStatus;
  status_changed_at: string;
  corrections: ManualReviewCorrectionFieldResponse[];
  action: ManualReviewAction;
}

export interface ManualReviewResubmitRequest {
  performed_by_user_id: string;
  document_id?: string | null;
  target_status: "decision_ready" | "queued_for_processing";
  comment?: string | null;
  reason_code?: string | null;
  evidence_refs?: EvidenceReference[];
}

export interface ManualReviewWorkflowResponse {
  case_id: string;
  case_status: CaseStatus;
  status_changed_at: string;
  allowed_next_statuses: CaseStatus[];
  action: ManualReviewAction;
}

export interface AuditEvent {
  id: string;
  case_id?: string | null;
  actor_id?: string | null;
  actor_user_id?: string | null;
  actor_type: AuditActorType;
  actor_identifier?: string | null;
  event_type: AuditEventType;
  summary: string;
  message?: string;
  resource_type: string;
  entity_type?: string;
  resource_id: string;
  entity_id?: string | null;
  occurred_at: string;
  metadata: Record<string, unknown>;
  details?: Record<string, unknown>;
  evidence_refs: EvidenceReference[];
  created_at?: string;
  updated_at?: string;
}

export interface CaseSummary {
  id: string;
  case_reference: string;
  case_type: string;
  status: CaseStatus;
  status_changed_at: string;
  current_queue: string;
  source_channel: string;
  customer_reference?: string | null;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface CaseDetail {
  id: string;
  case_reference: string;
  case_type: string;
  status: CaseStatus;
  status_changed_at: string;
  current_queue: string;
  source_channel: string;
  customer_reference?: string | null;
  created_at: string;
  updated_at: string;
  submitted_by_user?: {
    id: string;
    username: string;
    email: string;
    display_name: string;
    status: string;
    roles: Array<{ id: string; code: string; name: string; description?: string | null }>;
  } | null;
  metadata: Record<string, string>;
  documents: DocumentUploadMetadata[];
  ocr_results: OCRResult[];
  extraction_results: ExtractionResult[];
  validation: ValidationResult;
  decisions: Decision[];
  manual_review_actions: ManualReviewAction[];
  audit_events: AuditEvent[];
  closed_at?: string | null;
}

export interface CaseListResponse {
  items: CaseSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface AuditEventListResponse {
  items: AuditEvent[];
  total: number;
  limit: number;
  offset: number;
}

export interface CaseCreateRequest {
  case_reference: string;
  case_type: string;
  customer_reference?: string | null;
  source_channel?: string;
  current_queue?: string;
  case_metadata?: Record<string, unknown>;
  actor_id?: string | null;
}

export interface CaseStatusTransitionRequest {
  to_status: CaseStatus;
  actor_type?: AuditActorType;
  actor_id?: string | null;
  reason_code?: string | null;
  comment?: string | null;
  metadata?: Record<string, unknown>;
}

export interface CaseStatusTransitionResponse {
  case_id: string;
  from_status: CaseStatus;
  to_status: CaseStatus;
  transition_name: string;
  status_changed_at: string;
}

export interface QueueProcessingRequest {
  actor_id?: string | null;
  reason_code?: string | null;
  run_synchronously?: boolean | null;
}

export interface QueueProcessingResponse {
  case_id: string;
  status: CaseStatus;
  correlation_id?: string | null;
  attempt_number?: number | null;
  processed_document_count?: number | null;
  validation_finding_count?: number | null;
  risk_finding_count?: number | null;
  compliance_finding_count?: number | null;
  manual_review_required?: boolean | null;
  decision_id?: string | null;
}

export interface DecisionCreateRequest {
  outcome: DecisionOutcome;
  rationale: string;
  evidence_refs?: EvidenceReference[];
  decision_metadata?: Record<string, unknown>;
  actor_id: string;
}

export interface ApiErrorDetail {
  field?: string | null;
  issue: string;
  context: Record<string, unknown>;
}

export interface ApiErrorPayload {
  code: string;
  message: string;
  trace_id?: string | null;
  details: ApiErrorDetail[];
}

export interface ApiErrorEnvelope {
  error: ApiErrorPayload;
}

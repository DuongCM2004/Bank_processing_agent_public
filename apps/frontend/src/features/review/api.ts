import { apiClient } from "@/api/client";
import type {
  EvidenceReference,
  ManualCorrectionSubmissionRequest,
  ManualCorrectionSubmissionResponse,
  ManualReviewAction,
  ManualReviewActionType,
  ManualReviewNoteRequest,
  ManualReviewResubmitRequest,
  ManualReviewWorkflowResponse,
} from "@/api/contracts";
import { listCases } from "@/features/cases/api";

export function listManualReviewCases() {
  return listCases({ status: "manual_review_required", limit: 25, offset: 0 });
}

// Backend shape for ManualReviewActionResponse (see apps/backend/src/ops_agent/api/schemas.py).
// The backend uses `performed_by_user_id`; the frontend surface also exposes
// `reviewer_id` as an alias so existing UI code keeps working.
interface BackendManualReviewAction {
  id: string;
  case_id: string;
  document_id?: string | null;
  performed_by_user_id: string;
  related_decision_id?: string | null;
  action_type: ManualReviewActionType;
  comment?: string | null;
  payload: Record<string, unknown>;
  evidence_refs: readonly EvidenceReference[];
  created_at: string;
  updated_at: string;
}

interface BackendManualCorrectionSubmissionResponse {
  case_id: string;
  case_status: ManualCorrectionSubmissionResponse["case_status"];
  status_changed_at: string;
  corrections: ManualCorrectionSubmissionResponse["corrections"];
  action: BackendManualReviewAction;
}

interface BackendManualReviewWorkflowResponse {
  case_id: string;
  case_status: ManualReviewWorkflowResponse["case_status"];
  status_changed_at: string;
  allowed_next_statuses: ManualReviewWorkflowResponse["allowed_next_statuses"];
  action: BackendManualReviewAction;
}

function normalizeManualReviewAction(action: BackendManualReviewAction): ManualReviewAction {
  return {
    id: action.id,
    case_id: action.case_id,
    document_id: action.document_id,
    performed_by_user_id: action.performed_by_user_id,
    reviewer_id: action.performed_by_user_id,
    related_decision_id: action.related_decision_id ?? null,
    action_type: action.action_type,
    comment: action.comment,
    payload: action.payload,
    evidence_refs: action.evidence_refs,
    created_at: action.created_at,
    updated_at: action.updated_at,
  };
}

export function addManualReviewNote(
  caseId: string,
  request: ManualReviewNoteRequest,
): Promise<ManualReviewAction> {
  return apiClient
    .post<BackendManualReviewAction, ManualReviewNoteRequest>(
      `/cases/${caseId}/manual-review/notes`,
      request,
    )
    .then(normalizeManualReviewAction);
}

export function submitManualCorrections(
  caseId: string,
  request: ManualCorrectionSubmissionRequest,
): Promise<ManualCorrectionSubmissionResponse> {
  return apiClient
    .post<BackendManualCorrectionSubmissionResponse, ManualCorrectionSubmissionRequest>(
      `/cases/${caseId}/manual-review/corrections`,
      request,
    )
    .then((response) => ({
      case_id: response.case_id,
      case_status: response.case_status,
      status_changed_at: response.status_changed_at,
      corrections: response.corrections,
      action: normalizeManualReviewAction(response.action),
    }));
}

export function resubmitManualReviewCase(
  caseId: string,
  request: ManualReviewResubmitRequest,
): Promise<ManualReviewWorkflowResponse> {
  return apiClient
    .post<BackendManualReviewWorkflowResponse, ManualReviewResubmitRequest>(
      `/cases/${caseId}/manual-review/resubmit`,
      request,
    )
    .then((response) => ({
      case_id: response.case_id,
      case_status: response.case_status,
      status_changed_at: response.status_changed_at,
      allowed_next_statuses: response.allowed_next_statuses,
      action: normalizeManualReviewAction(response.action),
    }));
}

import { apiClient } from "@/api/client";
import type {
  CaseStatusTransitionRequest,
  ManualCorrectionSubmissionRequest,
  ManualCorrectionSubmissionResponse,
  ManualReviewAction,
  ManualReviewActionCreateRequest,
  ManualReviewNoteRequest,
  ManualReviewResubmitRequest,
  ManualReviewWorkflowResponse,
} from "@/api/contracts";
import { listCases, transitionCaseStatus } from "@/features/cases/api";

export function listManualReviewCases() {
  return listCases({ status: "manual_review_required", limit: 25, offset: 0 });
}

interface BackendManualReviewAction {
  id: string;
  case_id: string;
  document_id?: string | null;
  action_type: ManualReviewAction["action_type"];
  reviewer_id: string;
  comment?: string | null;
  payload: Record<string, unknown>;
  evidence_refs: ManualReviewAction["evidence_refs"];
  created_at: string;
  updated_at: string;
}

function normalizeManualReviewAction(action: BackendManualReviewAction): ManualReviewAction {
  return {
    id: action.id,
    case_id: action.case_id,
    document_id: action.document_id,
    performed_by_user_id: action.reviewer_id,
    reviewer_id: action.reviewer_id,
    related_decision_id: null,
    action_type: action.action_type,
    comment: action.comment,
    payload: action.payload,
    evidence_refs: action.evidence_refs,
    created_at: action.created_at,
    updated_at: action.updated_at,
  };
}

export function recordManualReviewAction(caseId: string, request: ManualReviewActionCreateRequest) {
  return apiClient
    .post<BackendManualReviewAction, ManualReviewActionCreateRequest>(`/cases/${caseId}/manual-review/actions`, request)
    .then(normalizeManualReviewAction);
}

export function addManualReviewNote(caseId: string, request: ManualReviewNoteRequest) {
  return recordManualReviewAction(caseId, {
    document_id: request.document_id,
    action_type: "add_note",
    reviewer_id: request.performed_by_user_id,
    comment: request.comment,
    payload: {},
    evidence_refs: request.evidence_refs ?? [],
  });
}

export function submitManualCorrections(caseId: string, request: ManualCorrectionSubmissionRequest) {
  return recordManualReviewAction(caseId, {
    document_id: request.document_id,
    action_type: "correct_data",
    reviewer_id: request.performed_by_user_id,
    comment: request.comment,
    payload: { corrections: request.corrections },
    evidence_refs: request.evidence_refs ?? [],
  }).then(
    (action): ManualCorrectionSubmissionResponse => ({
      case_id: caseId,
      case_status: "manual_review_required",
      status_changed_at: action.created_at,
      corrections: request.corrections.map((correction) => ({
        ...correction,
        evidence_refs: correction.evidence_refs ?? [],
      })),
      action,
    }),
  );
}

export function resubmitManualReviewCase(caseId: string, request: ManualReviewResubmitRequest) {
  const actionType = request.target_status === "queued_for_processing" ? "request_reprocessing" : "confirm_extraction";
  const transitionRequest: CaseStatusTransitionRequest = {
    to_status: request.target_status,
    actor_type: "user",
    actor_id: request.performed_by_user_id,
    reason_code: request.reason_code ?? (request.target_status === "decision_ready" ? "manual_review_completed" : "manual_reprocessing_requested"),
    comment: request.comment,
  };

  return recordManualReviewAction(caseId, {
    document_id: request.document_id,
    action_type: actionType,
    reviewer_id: request.performed_by_user_id,
    comment: request.comment,
    payload: { target_status: request.target_status },
    evidence_refs: request.evidence_refs ?? [],
  })
    .then((action) => {
      if (request.target_status === "queued_for_processing") {
        return {
          case_id: caseId,
          case_status: request.target_status,
          status_changed_at: action.created_at,
          allowed_next_statuses: [],
          action,
        };
      }

      return transitionCaseStatus(caseId, transitionRequest).then(
        (transition): ManualReviewWorkflowResponse => ({
          case_id: caseId,
          case_status: transition.to_status,
          status_changed_at: transition.status_changed_at,
          allowed_next_statuses: [],
          action,
        }),
      );
    });
}

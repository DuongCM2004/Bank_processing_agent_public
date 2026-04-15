import { apiClient } from "@/api/client";
import type {
  ManualCorrectionSubmissionRequest,
  ManualCorrectionSubmissionResponse,
  ManualReviewNoteRequest,
  ManualReviewResubmitRequest,
  ManualReviewWorkflowResponse,
} from "@/api/contracts";
import { listCases } from "@/features/cases/api";

export function listManualReviewCases() {
  return listCases({ status: "manual_review_required", limit: 25, offset: 0 });
}

export function addManualReviewNote(caseId: string, request: ManualReviewNoteRequest) {
  return apiClient.post<ManualReviewWorkflowResponse["action"], ManualReviewNoteRequest>(
    `/cases/${caseId}/manual-review/notes`,
    request,
  );
}

export function submitManualCorrections(caseId: string, request: ManualCorrectionSubmissionRequest) {
  return apiClient.post<ManualCorrectionSubmissionResponse, ManualCorrectionSubmissionRequest>(
    `/cases/${caseId}/manual-review/corrections`,
    request,
  );
}

export function resubmitManualReviewCase(caseId: string, request: ManualReviewResubmitRequest) {
  return apiClient.post<ManualReviewWorkflowResponse, ManualReviewResubmitRequest>(
    `/cases/${caseId}/manual-review/resubmit`,
    request,
  );
}

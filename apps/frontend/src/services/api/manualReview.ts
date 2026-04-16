import { apiClient } from "@/services/api/client";
import type {
  ManualCorrectionSubmissionRequest,
  ManualCorrectionSubmissionResponse,
  ManualReviewAction,
  ManualReviewNoteRequest,
  ManualReviewResubmitRequest,
  ManualReviewWorkflowResponse,
} from "@/types/api";

export function addManualReviewNote(caseId: string, request: ManualReviewNoteRequest) {
  return apiClient.post<ManualReviewAction, ManualReviewNoteRequest>(`/cases/${caseId}/manual-review/notes`, request);
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

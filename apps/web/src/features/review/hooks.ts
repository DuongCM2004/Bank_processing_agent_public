import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type {
  ManualCorrectionSubmissionRequest,
  ManualReviewNoteRequest,
  ManualReviewResubmitRequest,
} from "@/api/contracts";
import {
  addManualReviewNote,
  listManualReviewCases,
  resubmitManualReviewCase,
  submitManualCorrections,
} from "@/features/review/api";

export function useManualReviewCasesQuery() {
  return useQuery({
    queryKey: ["manual-review-cases"],
    queryFn: listManualReviewCases,
  });
}

function invalidateManualReviewQueries(queryClient: ReturnType<typeof useQueryClient>, caseId: string) {
  void queryClient.invalidateQueries({ queryKey: ["case-workspace", caseId] });
  void queryClient.invalidateQueries({ queryKey: ["case-detail", caseId] });
  void queryClient.invalidateQueries({ queryKey: ["manual-review-cases"] });
}

export function useAddManualReviewNoteMutation(caseId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ManualReviewNoteRequest) => addManualReviewNote(caseId!, request),
    onSuccess: () => {
      if (caseId) {
        invalidateManualReviewQueries(queryClient, caseId);
      }
    },
  });
}

export function useSubmitManualCorrectionsMutation(caseId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ManualCorrectionSubmissionRequest) => submitManualCorrections(caseId!, request),
    onSuccess: () => {
      if (caseId) {
        invalidateManualReviewQueries(queryClient, caseId);
      }
    },
  });
}

export function useResubmitManualReviewCaseMutation(caseId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ManualReviewResubmitRequest) => resubmitManualReviewCase(caseId!, request),
    onSuccess: () => {
      if (caseId) {
        invalidateManualReviewQueries(queryClient, caseId);
      }
    },
  });
}

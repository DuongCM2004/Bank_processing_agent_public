import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { DocumentReviewRequest } from "@/api/contracts";
import { getDocumentExtraction, getDocumentStatus, reviewDocument } from "@/features/documents/api";

export function useDocumentStatusQuery(documentId: string | undefined) {
  return useQuery({
    queryKey: ["document-status", documentId],
    queryFn: () => getDocumentStatus(documentId!),
    enabled: Boolean(documentId),
  });
}

export function useDocumentExtractionQuery(documentId: string | undefined) {
  return useQuery({
    queryKey: ["document-extraction", documentId],
    queryFn: () => getDocumentExtraction(documentId!),
    enabled: Boolean(documentId),
  });
}

export function useReviewDocumentMutation(caseId: string | undefined, documentId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: DocumentReviewRequest) => reviewDocument(documentId!, request),
    onSuccess: () => {
      if (documentId) {
        void queryClient.invalidateQueries({ queryKey: ["document-status", documentId] });
        void queryClient.invalidateQueries({ queryKey: ["document-extraction", documentId] });
        void queryClient.invalidateQueries({ queryKey: ["uuid-audit-events", documentId] });
      }
      if (caseId) {
        void queryClient.invalidateQueries({ queryKey: ["case-workspace", caseId] });
        void queryClient.invalidateQueries({ queryKey: ["case-detail", caseId] });
      }
    },
  });
}

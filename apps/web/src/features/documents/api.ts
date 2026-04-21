import { apiClient } from "@/api/client";
import type {
  DocumentExtractionResponse,
  DocumentReviewRequest,
  DocumentReviewResponse,
  DocumentStatusResponse,
} from "@/api/contracts";

export function getDocumentStatus(documentId: string) {
  return apiClient.get<DocumentStatusResponse>(`/documents/${documentId}/status`);
}

export function getDocumentExtraction(documentId: string) {
  return apiClient.get<DocumentExtractionResponse>(`/documents/${documentId}/extraction`);
}

export function reviewDocument(documentId: string, request: DocumentReviewRequest) {
  return apiClient.post<DocumentReviewResponse, DocumentReviewRequest>(`/documents/${documentId}/review`, request);
}

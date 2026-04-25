import { apiClient } from "@/api/client";
import type {
  DocumentExtractionResponse,
  DocumentReviewRequest,
  DocumentReviewResponse,
  DocumentStatusResponse,
  IdentityDocumentExtraction,
} from "@/api/contracts";

export function previewDocumentExtraction(file: File, documentType = "identity_document") {
  const form = new FormData();
  form.append("file", file);
  form.append("document_type", documentType);
  return apiClient.postForm<IdentityDocumentExtraction>("/documents/extract-preview", form, {
    timeoutMs: 120_000,
  });
}

export function getDocumentStatus(documentId: string) {
  return apiClient.get<DocumentStatusResponse>(`/documents/${documentId}/status`);
}

export function getDocumentExtraction(documentId: string) {
  return apiClient.get<DocumentExtractionResponse>(`/documents/${documentId}/extraction`);
}

export function reviewDocument(documentId: string, request: DocumentReviewRequest) {
  return apiClient.post<DocumentReviewResponse, DocumentReviewRequest>(`/documents/${documentId}/review`, request);
}

import { apiClient } from "@/services/api/client";
import type { CaseDetail, CaseListResponse, CaseStatus } from "@/types/api";

export interface ListCasesParams {
  limit?: number;
  offset?: number;
  status?: CaseStatus;
  currentQueue?: string;
  caseType?: string;
}

export function listCases(params: ListCasesParams = {}) {
  return apiClient.get<CaseListResponse>("/cases", {
    limit: params.limit ?? 20,
    offset: params.offset ?? 0,
    status: params.status,
    current_queue: params.currentQueue,
    case_type: params.caseType,
  });
}

export function getCaseDetail(caseId: string) {
  return apiClient.get<CaseDetail>(`/cases/${caseId}/detail`);
}

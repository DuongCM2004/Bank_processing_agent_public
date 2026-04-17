import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { CaseCreateRequest, CaseStatus, CaseStatusTransitionRequest, DecisionCreateRequest, QueueProcessingRequest } from "@/api/contracts";
import {
  createCase,
  createDecision,
  getCaseDetail,
  listCases,
  queueCaseProcessing,
  transitionCaseStatus,
  uploadCaseDocument,
} from "@/features/cases/api";
import { buildCaseWorkspaceViewModel } from "@/features/cases/workspace";

interface UseCasesQueryFilters {
  status?: CaseStatus;
  limit?: number;
  offset?: number;
  currentQueue?: string;
  caseType?: string;
}

export function useCasesQuery(filters?: UseCasesQueryFilters) {
  return useQuery({
    queryKey: ["cases", filters],
    queryFn: () => listCases(filters),
  });
}

export function useCaseDetailQuery(caseId: string | undefined) {
  return useQuery({
    queryKey: ["case-detail", caseId],
    queryFn: () => getCaseDetail(caseId!),
    enabled: Boolean(caseId),
  });
}

export function useCaseWorkspaceQuery(caseId: string | undefined) {
  return useQuery({
    queryKey: ["case-workspace", caseId],
    queryFn: () => getCaseDetail(caseId!),
    enabled: Boolean(caseId),
    select: buildCaseWorkspaceViewModel,
  });
}

export function useCreateCaseMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CaseCreateRequest) => createCase(request),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cases"] });
      void queryClient.invalidateQueries({ queryKey: ["manual-review-cases"] });
    },
  });
}

function invalidateCaseWorkspace(queryClient: ReturnType<typeof useQueryClient>, caseId: string) {
  void queryClient.invalidateQueries({ queryKey: ["case-workspace", caseId] });
  void queryClient.invalidateQueries({ queryKey: ["case-detail", caseId] });
  void queryClient.invalidateQueries({ queryKey: ["cases"] });
  void queryClient.invalidateQueries({ queryKey: ["manual-review-cases"] });
}

export function useTransitionCaseStatusMutation(caseId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CaseStatusTransitionRequest) => transitionCaseStatus(caseId!, request),
    onSuccess: () => {
      if (caseId) {
        invalidateCaseWorkspace(queryClient, caseId);
      }
    },
  });
}

export function useUploadCaseDocumentMutation(caseId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: { file: File; documentType: string; documentMetadata?: Record<string, unknown>; actorId?: string | null }) =>
      uploadCaseDocument(caseId!, request),
    onSuccess: () => {
      if (caseId) {
        invalidateCaseWorkspace(queryClient, caseId);
      }
    },
  });
}

export function useQueueCaseProcessingMutation(caseId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: QueueProcessingRequest) => queueCaseProcessing(caseId!, request),
    onSuccess: () => {
      if (caseId) {
        invalidateCaseWorkspace(queryClient, caseId);
      }
    },
  });
}

export function useCreateDecisionMutation(caseId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: DecisionCreateRequest) => createDecision(caseId!, request),
    onSuccess: () => {
      if (caseId) {
        invalidateCaseWorkspace(queryClient, caseId);
      }
    },
  });
}

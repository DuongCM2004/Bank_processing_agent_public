import { useQuery } from "@tanstack/react-query";

import type { CaseStatus } from "@/api/contracts";
import { getCaseDetail, listCases } from "@/features/cases/api";
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

import { getCaseDetail, listCases, type ListCasesParams } from "@/services/api/cases";
import { buildCaseWorkspaceViewModel } from "@/utils/extraction";
import { useAsyncResource } from "@/hooks/useAsyncResource";

export function useCases(params: ListCasesParams) {
  return useAsyncResource(
    () => listCases(params),
    [params.limit, params.offset, params.status, params.currentQueue, params.caseType],
  );
}

export function useCaseWorkspace(caseId: string | undefined) {
  return useAsyncResource(
    () => {
      if (!caseId) {
        return Promise.reject(new Error("Case id is required."));
      }

      return getCaseDetail(caseId).then(buildCaseWorkspaceViewModel);
    },
    [caseId],
  );
}

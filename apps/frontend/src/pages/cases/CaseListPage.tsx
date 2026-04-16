import { useEffect, useMemo, useState } from "react";

import { AsyncBoundary } from "@/components/ui/StateBlock";
import { PageHeader } from "@/components/ui/PageHeader";
import { Panel } from "@/components/ui/Panel";
import { CaseFilters } from "@/features/case-list/components/CaseFilters";
import { CaseTable } from "@/features/case-list/components/CaseTable";
import { PaginationControls } from "@/features/case-list/components/PaginationControls";
import { useCases } from "@/hooks/useCases";
import type { CaseStatus } from "@/types/api";

const PAGE_SIZE = 10;

export function CaseListPage() {
  const [page, setPage] = useState(1);
  const [searchValue, setSearchValue] = useState("");
  const [status, setStatus] = useState<"all" | CaseStatus>("all");
  const [manualReviewOnly, setManualReviewOnly] = useState(false);

  const effectiveStatus = status === "all" ? (manualReviewOnly ? "manual_review_required" : undefined) : status;
  const casesResource = useCases({
    limit: PAGE_SIZE,
    offset: (page - 1) * PAGE_SIZE,
    status: effectiveStatus,
  });

  const visibleCases = useMemo(() => {
    const normalizedSearch = searchValue.trim().toLowerCase();
    return (casesResource.data?.items ?? []).filter((item) => {
      if (manualReviewOnly && item.status !== "manual_review_required") {
        return false;
      }

      if (!normalizedSearch) {
        return true;
      }

      return item.case_reference.toLowerCase().includes(normalizedSearch) || item.id.toLowerCase().includes(normalizedSearch);
    });
  }, [casesResource.data?.items, manualReviewOnly, searchValue]);

  useEffect(() => {
    setPage(1);
  }, [manualReviewOnly, status]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Case operations"
        title="Case queue"
        description="Review case status, document volume, queue ownership, and manual review requirements from a single operational list."
      />

      <Panel title="Active cases" description="Filterable backend-backed case list with pagination controls ready for queue triage.">
        <div className="space-y-5">
          <CaseFilters
            searchValue={searchValue}
            status={status}
            manualReviewOnly={manualReviewOnly}
            onSearchChange={setSearchValue}
            onStatusChange={setStatus}
            onManualReviewOnlyChange={setManualReviewOnly}
          />
          <AsyncBoundary
            isLoading={casesResource.isLoading}
            error={casesResource.error}
            isEmpty={visibleCases.length === 0}
            emptyTitle="No cases found"
            emptyMessage="The backend returned no cases for the current filter set."
            onRetry={casesResource.reload}
          >
            <div className="space-y-4">
              <CaseTable cases={visibleCases} />
              <PaginationControls
                page={page}
                pageSize={PAGE_SIZE}
                total={casesResource.data?.total ?? 0}
                onPageChange={setPage}
              />
            </div>
          </AsyncBoundary>
        </div>
      </Panel>
    </div>
  );
}

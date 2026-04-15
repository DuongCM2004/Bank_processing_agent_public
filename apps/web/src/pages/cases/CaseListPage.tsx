import { useEffect, useState } from "react";

import type { CaseStatus } from "@/api/contracts";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { AsyncContent } from "@/components/ui/AsyncContent";
import { CaseFilters } from "@/features/cases/components/CaseFilters";
import { CasePaginationControls } from "@/features/cases/components/CasePaginationControls";
import { CaseSummaryTable } from "@/features/cases/components/CaseSummaryTable";
import { useCasesQuery } from "@/features/cases/hooks";

const PAGE_SIZE = 10;

export function CaseListPage() {
  const [page, setPage] = useState(1);
  const [searchValue, setSearchValue] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | CaseStatus>("all");
  const [manualReviewOnly, setManualReviewOnly] = useState(false);

  const effectiveStatus = statusFilter === "all" ? (manualReviewOnly ? "manual_review_required" : undefined) : statusFilter;
  const casesQuery = useCasesQuery({
    limit: PAGE_SIZE,
    offset: (page - 1) * PAGE_SIZE,
    status: effectiveStatus,
  });

  const normalizedSearch = searchValue.trim().toLowerCase();
  const cases = (casesQuery.data?.items ?? []).filter((item) => {
    if (manualReviewOnly && item.status !== "manual_review_required") {
      return false;
    }

    if (!normalizedSearch) {
      return true;
    }

    return item.case_reference.toLowerCase().includes(normalizedSearch) || item.id.toLowerCase().includes(normalizedSearch);
  });

  useEffect(() => {
    setPage(1);
  }, [statusFilter, manualReviewOnly]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Cases"
        title="Case queue"
        description="Operational case list for triage, review ownership, queue paging, and navigation into the case workspace."
      />

      <Card
        title="All cases"
        description="Readable queue view for operations users with explicit workflow status, manual review visibility, and click-through into case detail."
      >
        <div className="space-y-5">
          <CaseFilters
            searchValue={searchValue}
            onSearchChange={setSearchValue}
            status={statusFilter}
            onStatusChange={setStatusFilter}
            manualReviewOnly={manualReviewOnly}
            onManualReviewOnlyChange={setManualReviewOnly}
          />

          <AsyncContent
            isLoading={casesQuery.isLoading}
            isError={casesQuery.isError}
            errorMessage="Case list could not be loaded."
            isEmpty={cases.length === 0}
            emptyTitle="No cases found"
            emptyMessage="No case records were returned by the backend."
            onRetry={() => void casesQuery.refetch()}
          >
            <div className="space-y-5">
              <CaseSummaryTable cases={cases} />
              <CasePaginationControls
                page={page}
                total={casesQuery.data?.total ?? 0}
                pageSize={PAGE_SIZE}
                onPageChange={setPage}
              />
            </div>
          </AsyncContent>
        </div>
      </Card>
    </div>
  );
}

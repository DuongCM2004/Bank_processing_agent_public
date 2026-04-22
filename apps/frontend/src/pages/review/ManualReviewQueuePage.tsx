import { Card } from "@/components/ui/Card";
import { AsyncContent } from "@/components/ui/AsyncContent";
import { PageHeader } from "@/components/ui/PageHeader";
import { CaseSummaryTable } from "@/features/cases/components/CaseSummaryTable";
import { useManualReviewCasesQuery } from "@/features/review/hooks";

export function ManualReviewQueuePage() {
  const reviewCasesQuery = useManualReviewCasesQuery();
  const cases = reviewCasesQuery.data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Manual review"
        title="Manual review queue"
        description="Prioritized queue of cases requiring explicit operator intervention before a final decision can be recorded."
      />

      <Card title="Cases awaiting review" description="Use this queue to open case workspaces, inspect evidence, and submit corrections or final decisions.">
        <AsyncContent
          isLoading={reviewCasesQuery.isLoading}
          isError={reviewCasesQuery.isError}
          errorMessage="Manual review cases could not be loaded."
          isEmpty={cases.length === 0}
          emptyTitle="Manual review queue is clear"
          emptyMessage="No cases currently require reviewer intervention."
          onRetry={() => void reviewCasesQuery.refetch()}
        >
          <CaseSummaryTable cases={cases} />
        </AsyncContent>
      </Card>
    </div>
  );
}

import { PageHeader } from "@/components/ui/PageHeader";
import { Panel } from "@/components/ui/Panel";
import { CaseTable } from "@/features/case-list/components/CaseTable";
import { AsyncBoundary } from "@/components/ui/StateBlock";
import { useCases } from "@/hooks/useCases";

export function ManualReviewQueuePage() {
  const casesResource = useCases({ status: "manual_review_required", limit: 25, offset: 0 });
  const items = casesResource.data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Manual review"
        title="Review queue"
        description="Focused queue for cases blocked on human review, correction, or workflow resubmission."
      />
      <Panel title="Cases requiring review" description="This view reuses the same case API with the manual review status filter applied.">
        <AsyncBoundary
          isLoading={casesResource.isLoading}
          error={casesResource.error}
          isEmpty={items.length === 0}
          emptyTitle="No manual review cases"
          emptyMessage="No cases are currently routed to manual review."
          onRetry={casesResource.reload}
        >
          <CaseTable cases={items} />
        </AsyncBoundary>
      </Panel>
    </div>
  );
}

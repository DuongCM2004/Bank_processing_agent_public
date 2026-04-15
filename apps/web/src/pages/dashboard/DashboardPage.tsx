import { Link } from "react-router-dom";

import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { AsyncContent } from "@/components/ui/AsyncContent";
import { CaseSummaryTable } from "@/features/cases/components/CaseSummaryTable";
import { useCasesQuery } from "@/features/cases/hooks";

export function DashboardPage() {
  const casesQuery = useCasesQuery({ limit: 5, offset: 0 });
  const cases = casesQuery.data?.items ?? [];

  const cards = [
    { label: "Visible cases", value: String(casesQuery.data?.total ?? 0) },
    { label: "Manual review queue", value: String(cases.filter((item) => item.status === "manual_review_required").length) },
    { label: "Decision ready", value: String(cases.filter((item) => item.status === "decision_ready").length) },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Overview"
        title="Operations dashboard"
        description="High-level queue visibility for the document processing workflow. Use this as the landing page for case triage and work allocation."
      />

      <div className="grid gap-4 md:grid-cols-3">
        {cards.map((card) => (
          <Card key={card.label}>
            <p className="eyebrow">{card.label}</p>
            <p className="mt-3 text-3xl font-semibold text-ink">{card.value}</p>
          </Card>
        ))}
      </div>

      <Card
        title="Recent cases"
        description="Latest visible cases across the operational queue."
        action={
          <Link to="/cases" className="text-sm font-semibold text-accent">
            View all cases
          </Link>
        }
      >
        <AsyncContent
          isLoading={casesQuery.isLoading}
          isError={casesQuery.isError}
          errorMessage="Recent cases could not be loaded."
          isEmpty={cases.length === 0}
          emptyTitle="No cases available"
          emptyMessage="Once the backend starts returning cases, they will appear here."
          onRetry={() => void casesQuery.refetch()}
        >
          <CaseSummaryTable cases={cases} />
        </AsyncContent>
      </Card>
    </div>
  );
}

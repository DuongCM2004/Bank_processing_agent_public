import { Link } from "react-router-dom";

import type { CaseSummary } from "@/api/contracts";
import { DataTable } from "@/components/ui/DataTable";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { CaseStatusBadge } from "@/features/cases/components/CaseStatusBadge";

function formatDateTime(value: string) {
  return new Date(value).toLocaleString();
}

function isManualReviewCase(item: CaseSummary) {
  return item.status === "manual_review_required";
}

export function CaseSummaryTable({ cases }: { cases: CaseSummary[] }) {
  return (
    <DataTable
      columns={[
        {
          key: "case_id",
          header: "Case ID",
          cell: (item) => (
            <div>
              <Link to={`/cases/${item.id}`} className="font-semibold text-ink underline-offset-4 hover:underline">
                {item.case_reference}
              </Link>
              <p className="mt-1 font-mono text-xs text-slate">{item.id}</p>
            </div>
          ),
          className: "min-w-[240px]",
        },
        {
          key: "status",
          header: "Status",
          cell: (item) => <CaseStatusBadge status={item.status} />,
          className: "min-w-[170px]",
        },
        {
          key: "created_at",
          header: "Created",
          cell: (item) => formatDateTime(item.created_at),
          className: "min-w-[180px]",
        },
        {
          key: "updated_at",
          header: "Latest update",
          cell: (item) => formatDateTime(item.updated_at),
          className: "min-w-[180px]",
        },
        {
          key: "documents",
          header: "Documents",
          cell: (item) => <span className="font-semibold text-ink">{item.document_count}</span>,
          className: "w-24",
        },
        {
          key: "manual_review_flag",
          header: "Manual review",
          cell: (item) =>
            isManualReviewCase(item) ? (
              <StatusBadge tone="warning">required</StatusBadge>
            ) : (
              <StatusBadge tone="neutral">clear</StatusBadge>
            ),
          className: "min-w-[150px]",
        },
      ]}
      rows={cases}
      getRowId={(item) => item.id}
    />
  );
}

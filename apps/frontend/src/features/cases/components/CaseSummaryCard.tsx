import type { CaseDetail } from "@/api/contracts";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { CaseStatusBadge } from "@/features/cases/components/CaseStatusBadge";

function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return "Not available";
  }

  return new Date(value).toLocaleString();
}

export function CaseSummaryCard({ caseDetail }: { caseDetail: CaseDetail }) {
  return (
    <Card title="Case summary" description="High-level case attributes used for operational review and routing.">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-line p-4">
          <p className="eyebrow">Case reference</p>
          <p className="mt-2 text-base font-semibold text-ink">{caseDetail.case_reference}</p>
          <p className="mt-1 font-mono text-xs text-slate">{caseDetail.id}</p>
        </div>

        <div className="rounded-2xl border border-line p-4">
          <p className="eyebrow">Current status</p>
          <div className="mt-2">
            <CaseStatusBadge status={caseDetail.status} />
          </div>
          <p className="mt-2 text-xs text-slate">Updated {formatDateTime(caseDetail.status_changed_at)}</p>
        </div>

        <div className="rounded-2xl border border-line p-4">
          <p className="eyebrow">Case metadata</p>
          <p className="mt-2 text-sm font-medium text-ink">{caseDetail.case_type}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <StatusBadge tone="neutral">{caseDetail.source_channel}</StatusBadge>
            <StatusBadge tone="active">{caseDetail.current_queue}</StatusBadge>
          </div>
        </div>

        <div className="rounded-2xl border border-line p-4">
          <p className="eyebrow">Timeline</p>
          <dl className="mt-2 space-y-2 text-sm text-slate">
            <div>
              <dt className="font-medium text-ink">Created</dt>
              <dd>{formatDateTime(caseDetail.created_at)}</dd>
            </div>
            <div>
              <dt className="font-medium text-ink">Latest update</dt>
              <dd>{formatDateTime(caseDetail.updated_at)}</dd>
            </div>
            <div>
              <dt className="font-medium text-ink">Closed</dt>
              <dd>{formatDateTime(caseDetail.closed_at)}</dd>
            </div>
          </dl>
        </div>
      </div>
    </Card>
  );
}

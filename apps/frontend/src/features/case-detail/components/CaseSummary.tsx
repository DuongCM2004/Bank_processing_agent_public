import { StatusBadge } from "@/components/ui/StatusBadge";
import { Panel } from "@/components/ui/Panel";
import type { CaseDetail } from "@/types/api";
import { formatDateTime } from "@/utils/format";
import { caseStatusTone } from "@/utils/status";

interface CaseSummaryProps {
  caseDetail: CaseDetail;
}

export function CaseSummary({ caseDetail }: CaseSummaryProps) {
  const facts = [
    ["Case type", caseDetail.case_type],
    ["Queue", caseDetail.current_queue],
    ["Source", caseDetail.source_channel],
    ["Customer", caseDetail.customer_reference ?? "Not provided"],
    ["Created", formatDateTime(caseDetail.created_at)],
    ["Status changed", formatDateTime(caseDetail.status_changed_at)],
  ];

  return (
    <Panel
      title="Case summary"
      description="High-signal case metadata used before a reviewer changes extracted values or workflow state."
      action={<StatusBadge label={caseDetail.status} tone={caseStatusTone(caseDetail.status)} />}
    >
      <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {facts.map(([label, value]) => (
          <div key={label} className="rounded-md border border-line bg-surface p-3">
            <dt className="text-xs font-bold uppercase tracking-wider text-muted">{label}</dt>
            <dd className="mt-1 text-sm font-semibold text-ink">{value}</dd>
          </div>
        ))}
      </dl>
    </Panel>
  );
}

import { Link } from "react-router-dom";

import { StatusBadge } from "@/components/ui/StatusBadge";
import type { CaseSummary } from "@/types/api";
import { formatDateTime } from "@/utils/format";
import { caseStatusTone } from "@/utils/status";

interface CaseTableProps {
  cases: CaseSummary[];
}

export function CaseTable({ cases }: CaseTableProps) {
  return (
    <div className="overflow-x-auto rounded-lg border border-line">
      <table className="min-w-full divide-y divide-line text-sm">
        <thead className="bg-surface text-left text-xs font-bold uppercase tracking-wider text-muted">
          <tr>
            <th className="px-4 py-3">Case</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Queue</th>
            <th className="px-4 py-3">Documents</th>
            <th className="px-4 py-3">Manual Review</th>
            <th className="px-4 py-3">Updated</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line bg-panel">
          {cases.map((item) => (
            <tr key={item.id} className="hover:bg-surface">
              <td className="px-4 py-3">
                <Link className="font-semibold text-blue hover:underline" to={`/cases/${item.id}`}>
                  {item.case_reference}
                </Link>
                <p className="mt-1 text-xs text-muted">{item.case_type}</p>
              </td>
              <td className="px-4 py-3">
                <StatusBadge label={item.status} tone={caseStatusTone(item.status)} />
              </td>
              <td className="px-4 py-3 text-ink">{item.current_queue}</td>
              <td className="px-4 py-3 font-mono text-ink">{item.document_count}</td>
              <td className="px-4 py-3">
                {item.status === "manual_review_required" ? (
                  <StatusBadge label="Required" tone="danger" />
                ) : (
                  <span className="text-muted">Not required</span>
                )}
              </td>
              <td className="px-4 py-3 text-muted">{formatDateTime(item.status_changed_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

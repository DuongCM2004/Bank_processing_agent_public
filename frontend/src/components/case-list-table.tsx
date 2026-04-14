import Link from "next/link";

import type { CaseRecord } from "@/lib/types";
import { EmptyState } from "@/components/empty-state";

function caseTone(status: CaseRecord["status"]): string {
  if (status === "failed" || status === "escalated") {
    return "danger";
  }
  if (status === "review_required" || status === "in_review" || status === "corrected") {
    return "warning";
  }
  return "safe";
}

export function CaseListTable({ cases }: { cases: CaseRecord[] }) {
  if (!cases.length) {
    return <EmptyState title="No cases in scope" detail="No active cases matched the current role and queue filters." />;
  }

  return (
    <section className="panel">
      <h2>Case List</h2>
      <p className="muted">Operational list view for reviewer assignment, exception routing, and case drill-down.</p>
      <table className="table">
        <thead>
          <tr>
            <th>Case</th>
            <th>Workflow</th>
            <th>Customer Ref</th>
            <th>Status</th>
            <th>Priority</th>
            <th>Queue</th>
            <th>Docs</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((item) => (
            <tr key={item.case_id}>
              <td>
                <Link href={`/cases/${item.case_id}`} className="table-link">
                  {item.case_id}
                </Link>
              </td>
              <td>{item.workflow_type}</td>
              <td>{item.customer_reference ?? "not provided"}</td>
              <td>
                <span className={`status-chip ${caseTone(item.status)}`}>{item.status}</span>
              </td>
              <td>{item.priority}</td>
              <td>{item.assigned_queue}</td>
              <td>{item.document_ids.length}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

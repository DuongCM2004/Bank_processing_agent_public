import { EmptyState } from "@/components/empty-state";
import type { ValidationResult } from "@/lib/types";

export function ValidationIssuesPanel({ validations }: { validations: ValidationResult[] }) {
  if (validations.length === 0) {
    return (
      <EmptyState
        title="No validation findings"
        detail="No blocking or warning rules have been recorded for the current case state."
      />
    );
  }

  return (
    <section className="panel">
      <h2>Validation Issues</h2>
      <p className="muted">Validation findings stay separate from extraction so blocking rules remain visible to reviewers.</p>
      <table className="table">
        <thead>
          <tr>
            <th>Rule</th>
            <th>Severity</th>
            <th>Result</th>
            <th>Reason</th>
            <th>Evidence</th>
          </tr>
        </thead>
        <tbody>
          {validations.map((item) => (
            <tr key={`${item.rule_id}-${item.reason_code}`}>
              <td>{item.rule_id}</td>
              <td>
                <span className={`status-chip ${item.severity === "critical" ? "danger" : item.severity === "info" ? "safe" : "warning"}`}>
                  {item.severity}
                </span>
              </td>
              <td>{item.result}</td>
              <td>{item.reason_code}</td>
              <td>{item.evidence_refs.length}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

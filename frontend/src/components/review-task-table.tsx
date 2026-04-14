import type { ReviewTask } from "@/lib/types";

function taskTone(task: ReviewTask): string {
  if (task.reason_codes.some((code) => code.includes("fraud") || code.includes("critical"))) {
    return "danger";
  }
  if (task.reason_codes.length > 0) {
    return "warning";
  }
  return "safe";
}

export function ReviewTaskTable({ tasks }: { tasks: ReviewTask[] }) {
  return (
    <div className="panel">
      <h2>Review Queue</h2>
      <p className="muted">Queue view optimized for manual triage, exception handling, and evidence-first routing.</p>
      <table className="table">
        <thead>
          <tr>
            <th>Case</th>
            <th>Status</th>
            <th>Queue</th>
            <th>Reasons</th>
            <th>Assignee</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr key={task.task_id}>
              <td>
                <strong>{task.case_id}</strong>
                <div className="muted">{task.task_id}</div>
              </td>
              <td>
                <span className={`status-chip ${taskTone(task)}`}>{task.status}</span>
              </td>
              <td>{task.assigned_queue}</td>
              <td>{task.reason_codes.join(", ") || "none"}</td>
              <td>{task.assigned_to ?? "unassigned"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

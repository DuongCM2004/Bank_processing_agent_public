import type { CaseWorkspaceData } from "@/lib/types";

export function CaseHeader({ workspace }: { workspace: CaseWorkspaceData }) {
  const { caseRecord, results, statusView, latestDecision, activeReviewTask } = workspace;

  return (
    <section className="page-header">
      <p className="eyebrow">Case Workspace</p>
      <h1>{caseRecord.case_id}</h1>
      <p className="muted">
        Reviewer workspace for source-vs-extracted comparison, exception resolution, and audited human actions.
      </p>
      <div className="stats-row">
        <span className="pill">Workflow: {caseRecord.workflow_type}</span>
        <span className="pill">Queue: {caseRecord.assigned_queue}</span>
        <span className="pill">Status: {caseRecord.status}</span>
        <span className="pill">Route: {results.recommended_route}</span>
        {statusView?.active_step ? <span className="pill">Step: {statusView.active_step}</span> : null}
        {latestDecision?.outcome ? <span className="pill">Decision: {latestDecision.outcome}</span> : null}
        {activeReviewTask?.task_id ? <span className="pill">Task: {activeReviewTask.task_id}</span> : null}
      </div>
    </section>
  );
}

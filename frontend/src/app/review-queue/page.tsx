import { AppShell } from "@/components/app-shell";
import { ReviewTaskTable } from "@/components/review-task-table";
import { demoUser } from "@/lib/mock-data";
import { listReviewTasks } from "@/lib/api";

export default async function ReviewQueuePage() {
  const tasks = await listReviewTasks();

  return (
    <AppShell user={demoUser}>
      <section className="shell">
        <section className="page-header">
          <p className="eyebrow">Reviewer Queue</p>
          <h1>Review Queue</h1>
          <p className="muted">
            Prioritizes ambiguous, risky, and policy-gated cases before any automation handoff.
          </p>
          <div className="pill-row">
            <span className="pill">evidence-linked</span>
            <span className="pill">human-review preserved</span>
            <span className="pill">audit-first</span>
          </div>
        </section>
        <ReviewTaskTable tasks={tasks} />
      </section>
    </AppShell>
  );
}

import { AppShell } from "@/components/app-shell";
import { CaseListTable } from "@/components/case-list-table";
import { demoUser } from "@/lib/mock-data";
import { listCases } from "@/lib/api";

export default async function CasesPage() {
  const cases = await listCases();

  return (
    <AppShell user={demoUser}>
      <section className="shell">
        <section className="page-header">
          <p className="eyebrow">Case Inventory</p>
          <h1>Cases</h1>
          <p className="muted">Primary ops list for triage, assignment, and review navigation.</p>
        </section>
        <CaseListTable cases={cases} />
      </section>
    </AppShell>
  );
}

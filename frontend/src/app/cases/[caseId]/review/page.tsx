import { CaseWorkspaceShell } from "@/components/case-workspace-shell";
import { ExtractionReviewPanel } from "@/components/extraction-review-panel";
import { ManualCorrectionPanel } from "@/components/manual-correction-panel";
import { RoleGate } from "@/components/role-gate";
import { ValidationIssuesPanel } from "@/components/validation-issues-panel";
import { canEditCorrections } from "@/lib/auth";
import { getCaseWorkspace } from "@/lib/api";
import { demoUser } from "@/lib/mock-data";

export default async function CaseReviewPage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = await params;
  const workspace = await getCaseWorkspace(caseId);

  return (
    <CaseWorkspaceShell workspace={workspace}>
      <section className="grid-2">
        <ExtractionReviewPanel fields={workspace.results.fields} />
        <ValidationIssuesPanel validations={workspace.results.validations} />
      </section>
      <RoleGate
        allowed={["ops_reviewer", "compliance_analyst", "supervisor"]}
        currentRole={demoUser.role}
        fallback={
          <section className="panel">
            <h2>Manual Correction Flow</h2>
            <p className="muted">Your role can inspect review context but cannot submit corrections.</p>
          </section>
        }
      >
        {canEditCorrections(demoUser.role) ? <ManualCorrectionPanel fields={workspace.results.fields} /> : null}
      </RoleGate>
    </CaseWorkspaceShell>
  );
}

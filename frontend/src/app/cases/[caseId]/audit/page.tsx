import { AuditHistoryPanel } from "@/components/audit-history-panel";
import { CaseWorkspaceShell } from "@/components/case-workspace-shell";
import { RoleGate } from "@/components/role-gate";
import { EmptyState } from "@/components/empty-state";
import { canViewAudit } from "@/lib/auth";
import { listAuditEvents, getCaseWorkspace } from "@/lib/api";
import { demoUser } from "@/lib/mock-data";

export default async function CaseAuditPage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = await params;
  const workspace = await getCaseWorkspace(caseId);
  const items = await listAuditEvents(caseId);

  return (
    <CaseWorkspaceShell workspace={workspace}>
      <RoleGate
        allowed={["ops_reviewer", "compliance_analyst", "supervisor", "platform_admin"]}
        currentRole={demoUser.role}
        fallback={<EmptyState title="Audit access restricted" detail="Your role does not have access to case audit history." />}
      >
        {canViewAudit(demoUser.role) ? <AuditHistoryPanel items={items} /> : null}
      </RoleGate>
    </CaseWorkspaceShell>
  );
}

import { CaseWorkspaceShell } from "@/components/case-workspace-shell";
import { DocumentViewerPanel } from "@/components/document-viewer-panel";
import { EvidenceDrawer } from "@/components/evidence-drawer";
import { getCaseWorkspace } from "@/lib/api";

export default async function CaseDocumentsPage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = await params;
  const workspace = await getCaseWorkspace(caseId);
  const evidence = workspace.results.fields.flatMap((field) => field.evidence_refs);

  return (
    <CaseWorkspaceShell workspace={workspace}>
      <section className="grid-2">
        <DocumentViewerPanel documents={workspace.documents} />
        <EvidenceDrawer evidence={evidence} />
      </section>
    </CaseWorkspaceShell>
  );
}

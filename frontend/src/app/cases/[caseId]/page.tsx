import { CaseWorkspaceShell } from "@/components/case-workspace-shell";
import { DocumentViewerPanel } from "@/components/document-viewer-panel";
import { ExtractionReviewPanel } from "@/components/extraction-review-panel";
import { ValidationIssuesPanel } from "@/components/validation-issues-panel";
import { getCaseWorkspace } from "@/lib/api";

export default async function CaseDetailsPage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = await params;
  const workspace = await getCaseWorkspace(caseId);

  return (
    <CaseWorkspaceShell workspace={workspace}>
      <section className="grid-2">
        <ExtractionReviewPanel fields={workspace.results.fields} />
        <DocumentViewerPanel documents={workspace.documents} />
      </section>
      <ValidationIssuesPanel validations={workspace.results.validations} />
    </CaseWorkspaceShell>
  );
}

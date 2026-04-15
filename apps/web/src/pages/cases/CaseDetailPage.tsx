import { useState } from "react";
import { useParams } from "react-router-dom";

import type { DocumentViewerEvidenceAnchor } from "@/features/documents/components/DocumentViewerShell";
import { AsyncContent } from "@/components/ui/AsyncContent";
import { PageHeader } from "@/components/ui/PageHeader";
import { AuditHistoryPanel } from "@/features/audit/components/AuditHistoryPanel";
import { CaseStatusBadge } from "@/features/cases/components/CaseStatusBadge";
import { CaseSummaryCard } from "@/features/cases/components/CaseSummaryCard";
import { DecisionSummaryCard } from "@/features/cases/components/DecisionSummaryCard";
import { ExtractionSummaryCard } from "@/features/cases/components/ExtractionSummaryCard";
import { ManualReviewStatusCard } from "@/features/cases/components/ManualReviewStatusCard";
import { useCaseWorkspaceQuery } from "@/features/cases/hooks";
import { DocumentViewerShell } from "@/features/documents/components/DocumentViewerShell";
import { ExtractionReviewPanel } from "@/features/review/components/ExtractionReviewPanel";
import { FindingsPanel } from "@/features/review/components/FindingsPanel";
import { ManualReviewFlowPanel } from "@/features/review/components/ManualReviewFlowPanel";
import {
  useAddManualReviewNoteMutation,
  useResubmitManualReviewCaseMutation,
  useSubmitManualCorrectionsMutation,
} from "@/features/review/hooks";

function buildEvidenceAnchors(
  extractionResults: Array<{
    id: string;
    schema_name: string;
    evidence_refs: Array<{
      document_id: string;
      page_number?: number | null;
      extracted_value?: string | null;
      metadata: Record<string, string>;
    }>;
  }>,
): DocumentViewerEvidenceAnchor[] {
  return extractionResults.flatMap((result) =>
    result.evidence_refs.map((reference, index) => ({
      id: `${result.id}-${index}`,
      documentId: reference.document_id,
      label: reference.metadata.field_name ?? result.schema_name,
      pageNumber: reference.page_number,
      extractedValue: reference.extracted_value,
      metadata: reference.metadata,
    })),
  );
}

export function CaseDetailPage() {
  const { caseId } = useParams();
  const caseQuery = useCaseWorkspaceQuery(caseId);
  const workspace = caseQuery.data;
  const evidenceAnchors = workspace ? buildEvidenceAnchors(workspace.caseDetail.extraction_results) : [];
  const [selectedCorrectionFieldId, setSelectedCorrectionFieldId] = useState<string | null>(null);
  const addNoteMutation = useAddManualReviewNoteMutation(caseId);
  const submitCorrectionsMutation = useSubmitManualCorrectionsMutation(caseId);
  const resubmitMutation = useResubmitManualReviewCaseMutation(caseId);

  return (
    <div className="space-y-6">
      <AsyncContent
        isLoading={caseQuery.isLoading}
        isError={caseQuery.isError}
        errorMessage="The case detail could not be loaded."
        isEmpty={!workspace}
        emptyTitle="Case not found"
        emptyMessage="The requested case was not returned by the backend."
        onRetry={() => void caseQuery.refetch()}
      >
        {workspace ? (
          <>
            <PageHeader
              eyebrow="Case workspace"
              title={workspace.caseDetail.case_reference}
              description={`Review all processing outputs, findings, manual actions, decisions, and audit evidence for ${workspace.caseDetail.case_type}.`}
              action={<CaseStatusBadge status={workspace.caseDetail.status} />}
            />

            <CaseSummaryCard caseDetail={workspace.caseDetail} />

            <div className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.95fr)]">
              <div className="space-y-6">
                <DocumentViewerShell
                  documents={workspace.caseDetail.documents}
                  previewMode="pdf"
                  evidenceAnchors={evidenceAnchors}
                />
                <ExtractionSummaryCard
                  totalResults={workspace.extractionSummary.totalResults}
                  completedResults={workspace.extractionSummary.completedResults}
                  averageConfidence={workspace.extractionSummary.averageConfidence}
                  schemas={workspace.extractionSummary.schemas}
                  results={workspace.extractionSummary.results}
                />
                <ExtractionReviewPanel
                  totalFields={workspace.extractionReview.totalFields}
                  attentionCount={workspace.extractionReview.attentionCount}
                  missingCount={workspace.extractionReview.missingCount}
                  ambiguousCount={workspace.extractionReview.ambiguousCount}
                  fields={workspace.extractionReview.fields}
                  onRequestCorrection={(field) => setSelectedCorrectionFieldId(field.id)}
                />
                <FindingsPanel
                  validationFindings={workspace.caseDetail.validation.validation_findings}
                  riskFindings={workspace.caseDetail.validation.risk_findings}
                  complianceFindings={workspace.caseDetail.validation.compliance_findings}
                />
              </div>

              <div className="space-y-6">
                <ManualReviewStatusCard
                  caseStatus={workspace.caseDetail.status}
                  latestAction={workspace.latestManualReviewAction}
                  actionCount={workspace.caseDetail.manual_review_actions.length}
                />
                <ManualReviewFlowPanel
                  caseStatus={workspace.caseDetail.status}
                  fields={workspace.extractionReview.fields}
                  actions={workspace.caseDetail.manual_review_actions}
                  selectedFieldId={selectedCorrectionFieldId}
                  onSelectedFieldChange={setSelectedCorrectionFieldId}
                  onAddNote={(request) => addNoteMutation.mutateAsync(request)}
                  onSubmitCorrections={(request) => submitCorrectionsMutation.mutateAsync(request)}
                  onResubmit={(request) => resubmitMutation.mutateAsync(request)}
                  isSubmittingNote={addNoteMutation.isPending}
                  isSubmittingCorrections={submitCorrectionsMutation.isPending}
                  isSubmittingWorkflow={resubmitMutation.isPending}
                />
                <DecisionSummaryCard decisions={workspace.caseDetail.decisions} />
                <AuditHistoryPanel
                  events={workspace.auditPreview.recentEvents}
                  totalEvents={workspace.auditPreview.totalEvents}
                  title="Audit history preview"
                  description="Recent structured audit activity. Full timeline can be expanded later without changing the section contract."
                  emptyMessage="No audit activity available."
                />
              </div>
            </div>
          </>
        ) : null}
      </AsyncContent>
    </div>
  );
}

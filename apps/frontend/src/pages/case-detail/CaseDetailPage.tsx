import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import { AsyncBoundary } from "@/components/ui/StateBlock";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { AuditHistoryPanel } from "@/features/audit-history/AuditHistoryPanel";
import { CaseSummary } from "@/features/case-detail/components/CaseSummary";
import { DecisionSummary } from "@/features/case-detail/components/DecisionSummary";
import { ExtractionSummary } from "@/features/case-detail/components/ExtractionSummary";
import { DocumentViewerShell, type EvidenceAnchor } from "@/features/document-viewer/DocumentViewerShell";
import { ExtractionReviewPanel } from "@/features/extraction-review/ExtractionReviewPanel";
import { ManualReviewPanel } from "@/features/manual-review/ManualReviewPanel";
import { ValidationFindingsPanel } from "@/features/validation-findings/ValidationFindingsPanel";
import { useCaseWorkspace } from "@/hooks/useCases";
import { caseStatusTone } from "@/utils/status";

export function CaseDetailPage() {
  const { caseId } = useParams();
  const caseResource = useCaseWorkspace(caseId);
  const workspace = caseResource.data;
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [selectedCorrectionFieldId, setSelectedCorrectionFieldId] = useState<string | null>(null);

  const evidenceAnchors = useMemo<EvidenceAnchor[]>(() => {
    if (!workspace) {
      return [];
    }

    return workspace.caseDetail.extraction_results.flatMap((result) =>
      result.evidence_refs.map((reference, index) => ({
        id: `${result.id}-${index}`,
        documentId: reference.document_id,
        label: reference.metadata.field_name ?? result.schema_name,
        pageNumber: reference.page_number,
        extractedValue: reference.extracted_value,
      })),
    );
  }, [workspace]);

  return (
    <div className="space-y-6">
      <AsyncBoundary
        isLoading={caseResource.isLoading}
        error={caseResource.error}
        isEmpty={!workspace}
        emptyTitle="Case not found"
        emptyMessage="The backend did not return a case detail payload for this id."
        onRetry={caseResource.reload}
      >
        {workspace ? (
          <>
            <PageHeader
              eyebrow="Case workspace"
              title={workspace.caseDetail.case_reference}
              description="Review linked documents, extraction output, validation findings, manual actions, decisions, and audit evidence."
              action={<StatusBadge label={workspace.caseDetail.status} tone={caseStatusTone(workspace.caseDetail.status)} />}
            />

            <CaseSummary caseDetail={workspace.caseDetail} />

            <div className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(340px,0.95fr)]">
              <div className="space-y-6">
                <DocumentViewerShell
                  documents={workspace.caseDetail.documents}
                  selectedDocumentId={selectedDocumentId}
                  onSelectDocument={setSelectedDocumentId}
                  evidenceAnchors={evidenceAnchors}
                />
                <ExtractionSummary
                  totalResults={workspace.extractionSummary.totalResults}
                  completedResults={workspace.extractionSummary.completedResults}
                  averageConfidence={workspace.extractionSummary.averageConfidence}
                  schemas={workspace.extractionSummary.schemas}
                />
                <ExtractionReviewPanel
                  totalFields={workspace.extractionReview.totalFields}
                  attentionCount={workspace.extractionReview.attentionCount}
                  missingCount={workspace.extractionReview.missingCount}
                  ambiguousCount={workspace.extractionReview.ambiguousCount}
                  fields={workspace.extractionReview.fields}
                  onRequestCorrection={(field) => setSelectedCorrectionFieldId(field.id)}
                />
                <ValidationFindingsPanel
                  validationFindings={workspace.caseDetail.validation.validation_findings}
                  riskFindings={workspace.caseDetail.validation.risk_findings}
                  complianceFindings={workspace.caseDetail.validation.compliance_findings}
                  hasBlockingFindings={workspace.caseDetail.validation.has_blocking_findings}
                />
              </div>

              <div className="space-y-6">
                <ManualReviewPanel
                  caseId={workspace.caseDetail.id}
                  caseStatus={workspace.caseDetail.status}
                  actions={workspace.caseDetail.manual_review_actions}
                  fields={workspace.extractionReview.fields}
                  selectedFieldId={selectedCorrectionFieldId}
                  onSelectedFieldChange={setSelectedCorrectionFieldId}
                  onSubmitted={caseResource.reload}
                />
                <DecisionSummary decisions={workspace.caseDetail.decisions} />
                <AuditHistoryPanel events={workspace.auditPreview.recentEvents} totalEvents={workspace.auditPreview.totalEvents} />
              </div>
            </div>
          </>
        ) : null}
      </AsyncBoundary>
    </div>
  );
}

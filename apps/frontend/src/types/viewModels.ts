import type { CaseDetail, Decision, ManualReviewAction } from "@/types/api";

export interface ExtractionReviewField {
  id: string;
  extractionResultId: string;
  documentId: string;
  schemaName: string;
  fieldName: string;
  rawValue: string | null;
  normalizedValue: string | null;
  confidence: number | null;
  evidenceSnippet: string | null;
  evidencePageNumber: number | null;
  isMissing: boolean;
  isAmbiguous: boolean;
  needsAttention: boolean;
}

export interface CaseWorkspaceViewModel {
  caseDetail: CaseDetail;
  latestDecision: Decision | null;
  latestManualReviewAction: ManualReviewAction | null;
  extractionReview: {
    totalFields: number;
    attentionCount: number;
    missingCount: number;
    ambiguousCount: number;
    fields: ExtractionReviewField[];
  };
  extractionSummary: {
    totalResults: number;
    completedResults: number;
    averageConfidence: number | null;
    schemas: string[];
  };
  auditPreview: {
    totalEvents: number;
    recentEvents: CaseDetail["audit_events"];
  };
}

import type { CaseDetail, Decision, EvidenceReference, ExtractionResult, ManualReviewAction } from "@/api/contracts";

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
  extractionSummary: {
    totalResults: number;
    completedResults: number;
    averageConfidence: number | null;
    schemas: string[];
    results: ExtractionResult[];
  };
  extractionReview: {
    totalFields: number;
    attentionCount: number;
    missingCount: number;
    ambiguousCount: number;
    fields: ExtractionReviewField[];
  };
  auditPreview: {
    totalEvents: number;
    recentEvents: CaseDetail["audit_events"];
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function formatValue(value: unknown): string | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : null;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    const items = value.map((item) => formatValue(item)).filter((item): item is string => Boolean(item));
    return items.length > 0 ? items.join(", ") : null;
  }

  if (isRecord(value)) {
    return JSON.stringify(value);
  }

  return null;
}

function extractEvidenceRefs(value: unknown): EvidenceReference[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is EvidenceReference => isRecord(item) && typeof item.document_id === "string");
}

function findMatchingEvidenceRef(result: ExtractionResult, fieldName: string, fieldValue: unknown): EvidenceReference | null {
  if (isRecord(fieldValue)) {
    const nestedEvidenceRefs = extractEvidenceRefs(fieldValue.evidence_refs ?? fieldValue.evidenceRefs);
    if (nestedEvidenceRefs.length > 0) {
      return nestedEvidenceRefs[0];
    }
  }

  return result.evidence_refs.find((reference) => reference.metadata.field_name === fieldName) ?? null;
}

function buildExtractionReviewFields(results: ExtractionResult[]): ExtractionReviewField[] {
  return results
    .flatMap((result) =>
      Object.entries(result.extracted_payload).map(([fieldName, fieldValue]) => {
        const fieldRecord = isRecord(fieldValue) ? fieldValue : null;
        const evidenceRef = findMatchingEvidenceRef(result, fieldName, fieldValue);
        const rawValue = fieldRecord
          ? formatValue(fieldRecord.raw_value ?? fieldRecord.rawValue ?? fieldRecord.value ?? fieldRecord.raw)
          : formatValue(fieldValue);
        const normalizedValue = fieldRecord
          ? formatValue(fieldRecord.normalized_value ?? fieldRecord.normalizedValue)
          : null;
        const confidenceValue =
          fieldRecord?.confidence ?? fieldRecord?.confidence_score ?? fieldRecord?.confidenceScore ?? result.confidence_score;
        const confidence = typeof confidenceValue === "number" ? confidenceValue : null;
        const isMissing = fieldRecord?.missing === true || rawValue === null;
        const isAmbiguous =
          fieldRecord?.ambiguous === true ||
          fieldRecord?.requires_review === true ||
          fieldRecord?.requiresReview === true ||
          (!isMissing && confidence !== null && confidence < 0.8);
        const needsAttention = isMissing || isAmbiguous;

        return {
          id: `${result.id}:${fieldName}`,
          extractionResultId: result.id,
          documentId: result.document_id,
          schemaName: result.schema_name,
          fieldName,
          rawValue,
          normalizedValue,
          confidence,
          evidenceSnippet: evidenceRef?.extracted_value ?? evidenceRef?.text_anchor ?? null,
          evidencePageNumber: evidenceRef?.page_number ?? null,
          isMissing,
          isAmbiguous,
          needsAttention,
        };
      }),
    )
    .sort((left, right) => {
      if (left.needsAttention !== right.needsAttention) {
        return left.needsAttention ? -1 : 1;
      }

      if (left.schemaName !== right.schemaName) {
        return left.schemaName.localeCompare(right.schemaName);
      }

      return left.fieldName.localeCompare(right.fieldName);
    });
}

export function buildCaseWorkspaceViewModel(caseDetail: CaseDetail): CaseWorkspaceViewModel {
  const extractionResults = caseDetail.extraction_results;
  const extractionReviewFields = buildExtractionReviewFields(extractionResults);
  const confidenceScores = extractionResults
    .map((result) => result.confidence_score)
    .filter((value): value is number => typeof value === "number");

  return {
    caseDetail,
    latestDecision: caseDetail.decisions[0] ?? null,
    latestManualReviewAction: caseDetail.manual_review_actions[0] ?? null,
    extractionSummary: {
      totalResults: extractionResults.length,
      completedResults: extractionResults.filter((result) => result.status === "completed").length,
      averageConfidence:
        confidenceScores.length > 0
          ? Number((confidenceScores.reduce((sum, value) => sum + value, 0) / confidenceScores.length).toFixed(2))
          : null,
      schemas: Array.from(new Set(extractionResults.map((result) => result.schema_name))),
      results: extractionResults,
    },
    extractionReview: {
      totalFields: extractionReviewFields.length,
      attentionCount: extractionReviewFields.filter((field) => field.needsAttention).length,
      missingCount: extractionReviewFields.filter((field) => field.isMissing).length,
      ambiguousCount: extractionReviewFields.filter((field) => field.isAmbiguous).length,
      fields: extractionReviewFields,
    },
    auditPreview: {
      totalEvents: caseDetail.audit_events.length,
      recentEvents: caseDetail.audit_events.slice(0, 5),
    },
  };
}

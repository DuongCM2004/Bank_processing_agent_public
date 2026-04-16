import type { CaseDetail, EvidenceReference, ExtractionResult } from "@/types/api";
import type { CaseWorkspaceViewModel, ExtractionReviewField } from "@/types/viewModels";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function formatFieldValue(value: unknown): string | null {
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
    const items = value.map(formatFieldValue).filter((item): item is string => Boolean(item));
    return items.length > 0 ? items.join(", ") : null;
  }

  if (isRecord(value)) {
    return JSON.stringify(value);
  }

  return null;
}

function evidenceRefsFrom(value: unknown): EvidenceReference[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is EvidenceReference => isRecord(item) && typeof item.document_id === "string");
}

function matchingEvidence(result: ExtractionResult, fieldName: string, fieldValue: unknown) {
  if (isRecord(fieldValue)) {
    const nestedRefs = evidenceRefsFrom(fieldValue.evidence_refs ?? fieldValue.evidenceRefs);
    if (nestedRefs.length > 0) {
      return nestedRefs[0];
    }
  }

  return result.evidence_refs.find((reference) => reference.metadata.field_name === fieldName) ?? null;
}

export function buildExtractionReviewFields(results: ExtractionResult[]): ExtractionReviewField[] {
  return results
    .flatMap((result) =>
      Object.entries(result.extracted_payload).map(([fieldName, fieldValue]) => {
        const fieldRecord = isRecord(fieldValue) ? fieldValue : null;
        const evidenceRef = matchingEvidence(result, fieldName, fieldValue);
        const rawValue = fieldRecord
          ? formatFieldValue(fieldRecord.raw_value ?? fieldRecord.rawValue ?? fieldRecord.raw ?? fieldRecord.value)
          : formatFieldValue(fieldValue);
        const normalizedValue = fieldRecord
          ? formatFieldValue(fieldRecord.normalized_value ?? fieldRecord.normalizedValue)
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
          needsAttention: isMissing || isAmbiguous,
        };
      }),
    )
    .sort((left, right) => {
      if (left.needsAttention !== right.needsAttention) {
        return left.needsAttention ? -1 : 1;
      }

      return `${left.schemaName}:${left.fieldName}`.localeCompare(`${right.schemaName}:${right.fieldName}`);
    });
}

export function buildCaseWorkspaceViewModel(caseDetail: CaseDetail): CaseWorkspaceViewModel {
  const fields = buildExtractionReviewFields(caseDetail.extraction_results);
  const confidenceScores = caseDetail.extraction_results
    .map((result) => result.confidence_score)
    .filter((value): value is number => typeof value === "number");

  return {
    caseDetail,
    latestDecision: caseDetail.decisions[0] ?? null,
    latestManualReviewAction: caseDetail.manual_review_actions[0] ?? null,
    extractionReview: {
      totalFields: fields.length,
      attentionCount: fields.filter((field) => field.needsAttention).length,
      missingCount: fields.filter((field) => field.isMissing).length,
      ambiguousCount: fields.filter((field) => field.isAmbiguous).length,
      fields,
    },
    extractionSummary: {
      totalResults: caseDetail.extraction_results.length,
      completedResults: caseDetail.extraction_results.filter((result) => result.status === "completed").length,
      averageConfidence:
        confidenceScores.length > 0
          ? confidenceScores.reduce((sum, value) => sum + value, 0) / confidenceScores.length
          : null,
      schemas: Array.from(new Set(caseDetail.extraction_results.map((result) => result.schema_name))),
    },
    auditPreview: {
      totalEvents: caseDetail.audit_events.length,
      recentEvents: caseDetail.audit_events.slice(0, 5),
    },
  };
}

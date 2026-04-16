import { describe, expect, it } from "vitest";

import { buildExtractionReviewFields } from "@/utils/extraction";
import type { ExtractionResult } from "@/types/api";

const result: ExtractionResult = {
  id: "ext-1",
  document_id: "doc-1",
  status: "completed",
  schema_name: "bank_statement",
  extracted_payload: {
    account_number: {
      raw_value: "123",
      normalized_value: "000123",
      confidence: 0.97,
    },
    missing_name: {
      raw_value: "",
      confidence: 0.4,
    },
  },
  confidence_score: 0.9,
  evidence_refs: [
    {
      document_id: "doc-1",
      page_number: 2,
      extracted_value: "123",
      text_anchor: null,
      metadata: { field_name: "account_number" },
    },
  ],
  provider_name: "extractor",
  created_at: "2026-04-16T09:00:00Z",
  updated_at: "2026-04-16T09:00:00Z",
};

describe("buildExtractionReviewFields", () => {
  it("normalizes field values and flags missing values first", () => {
    const fields = buildExtractionReviewFields([result]);

    expect(fields[0]).toMatchObject({
      fieldName: "missing_name",
      isMissing: true,
      needsAttention: true,
    });
    expect(fields[1]).toMatchObject({
      fieldName: "account_number",
      rawValue: "123",
      normalizedValue: "000123",
      evidencePageNumber: 2,
    });
  });
});

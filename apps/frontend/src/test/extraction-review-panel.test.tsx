import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ExtractionReviewPanel } from "@/features/extraction-review/ExtractionReviewPanel";
import type { ExtractionReviewField } from "@/types/viewModels";
import { renderWithProviders } from "@/test/render";

const fields: ExtractionReviewField[] = [
  {
    id: "field-1",
    extractionResultId: "ext-1",
    documentId: "doc-1",
    schemaName: "loan_application",
    fieldName: "borrower_name",
    rawValue: null,
    normalizedValue: null,
    confidence: 0.45,
    evidenceSnippet: null,
    evidencePageNumber: null,
    isMissing: true,
    isAmbiguous: false,
    needsAttention: true,
  },
];

describe("ExtractionReviewPanel", () => {
  it("shows missing markers and exposes correction action", async () => {
    const onRequestCorrection = vi.fn();
    renderWithProviders(
      <ExtractionReviewPanel
        totalFields={1}
        attentionCount={1}
        missingCount={1}
        ambiguousCount={0}
        fields={fields}
        onRequestCorrection={onRequestCorrection}
      />,
    );

    expect(screen.getAllByText("Missing").length).toBeGreaterThan(0);
    await userEvent.click(screen.getByRole("button", { name: "Correct" }));
    expect(onRequestCorrection).toHaveBeenCalledWith(fields[0]);
  });
});

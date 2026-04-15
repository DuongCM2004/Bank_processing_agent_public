import { fireEvent, screen } from "@testing-library/react";
import { vi } from "vitest";

import { ExtractionReviewPanel } from "@/features/review/components/ExtractionReviewPanel";
import { renderWithProviders } from "./render";

const fields = [
  {
    id: "ext-1:document_number",
    extractionResultId: "ext-1",
    documentId: "doc-1",
    schemaName: "passport_mvp",
    fieldName: "document_number",
    rawValue: "ABC123",
    normalizedValue: "ABC123",
    confidence: 0.94,
    evidenceSnippet: "ABC123",
    evidencePageNumber: 1,
    isMissing: false,
    isAmbiguous: false,
    needsAttention: false,
  },
  {
    id: "ext-1:expiry_date",
    extractionResultId: "ext-1",
    documentId: "doc-1",
    schemaName: "passport_mvp",
    fieldName: "expiry_date",
    rawValue: null,
    normalizedValue: null,
    confidence: 0.62,
    evidenceSnippet: null,
    evidencePageNumber: null,
    isMissing: true,
    isAmbiguous: true,
    needsAttention: true,
  },
] as const;

describe("ExtractionReviewPanel", () => {
  it("renders field values, uncertainty indicators, and correction actions", () => {
    const onRequestCorrection = vi.fn();

    renderWithProviders(
      <ExtractionReviewPanel
        totalFields={2}
        attentionCount={1}
        missingCount={1}
        ambiguousCount={1}
        fields={[...fields]}
        onRequestCorrection={onRequestCorrection}
      />,
    );

    expect(screen.getByText("Extraction review")).toBeInTheDocument();
    expect(screen.getByText("document number")).toBeInTheDocument();
    expect(screen.getAllByText("ABC123")).not.toHaveLength(0);
    expect(screen.getByText("94%")).toBeInTheDocument();
    expect(screen.getByText("missing")).toBeInTheDocument();
    expect(screen.getByText("ambiguous")).toBeInTheDocument();
    expect(screen.getByText("No extracted value")).toBeInTheDocument();
    expect(screen.getByText("No evidence snippet attached")).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole("button", { name: "Manual correction" })[0]);

    expect(onRequestCorrection).toHaveBeenCalledWith(fields[0]);
  });

  it("renders an empty state when there are no extracted fields", () => {
    renderWithProviders(
      <ExtractionReviewPanel
        totalFields={0}
        attentionCount={0}
        missingCount={0}
        ambiguousCount={0}
        fields={[]}
      />,
    );

    expect(screen.getByText("No extracted fields are available for review yet.")).toBeInTheDocument();
  });
});

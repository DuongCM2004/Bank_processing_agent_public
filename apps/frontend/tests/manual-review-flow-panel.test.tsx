import { fireEvent, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { ManualReviewFlowPanel } from "@/features/review/components/ManualReviewFlowPanel";
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
    confidence: 0.91,
    evidenceSnippet: "ABC123",
    evidencePageNumber: 1,
    isMissing: false,
    isAmbiguous: false,
    needsAttention: false,
  },
] as const;

const actions = [
  {
    id: "mra-1",
    case_id: "case-123",
    document_id: "doc-1",
    performed_by_user_id: "reviewer-7",
    related_decision_id: null,
    action_type: "add_note",
    comment: "Initial reviewer note.",
    payload: {},
    evidence_refs: [],
    created_at: "2026-04-15T10:00:00Z",
    updated_at: "2026-04-15T10:00:00Z",
  },
] as const;

describe("ManualReviewFlowPanel", () => {
  it("submits notes, corrections, and resubmission actions explicitly", async () => {
    const onAddNote = vi.fn().mockResolvedValue(undefined);
    const onSubmitCorrections = vi.fn().mockResolvedValue(undefined);
    const onResubmit = vi.fn().mockResolvedValue(undefined);

    renderWithProviders(
      <ManualReviewFlowPanel
        caseStatus="manual_review_required"
        fields={[...fields]}
        actions={[...actions]}
        onAddNote={onAddNote}
        onSubmitCorrections={onSubmitCorrections}
        onResubmit={onResubmit}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("user-123"), { target: { value: "reviewer-42" } });
    fireEvent.change(screen.getByPlaceholderText("Explain the reviewer observation or reason for holding the case."), {
      target: { value: "Need a second look at the passport." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Add reviewer note" }));

    await waitFor(() =>
      expect(onAddNote).toHaveBeenCalledWith({
        performed_by_user_id: "reviewer-42",
        comment: "Need a second look at the passport.",
      }),
    );

    fireEvent.change(screen.getByPlaceholderText("Enter corrected field value"), { target: { value: "ABC1234" } });
    fireEvent.click(screen.getByRole("button", { name: "Stage correction" }));
    expect(screen.getByText("Previous extracted value")).toBeInTheDocument();
    expect(screen.getByText("Pending corrected value")).toBeInTheDocument();
    expect(screen.getByText("After")).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText("Optional rationale for the submitted corrections."), {
      target: { value: "Verified against the scanned passport image." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Submit corrections" }));

    await waitFor(() =>
      expect(onSubmitCorrections).toHaveBeenCalledWith({
        performed_by_user_id: "reviewer-42",
        comment: "Verified against the scanned passport image.",
        corrections: [
          {
            extraction_result_id: "ext-1",
            field_name: "document_number",
            before_value: "ABC123",
            after_value: "ABC1234",
            evidence_refs: [],
          },
        ],
      }),
    );

    fireEvent.change(screen.getByLabelText("Resubmit target"), { target: { value: "queued_for_processing" } });
    fireEvent.change(screen.getByPlaceholderText("Optional resubmission note"), {
      target: { value: "Re-run extraction after reviewer correction." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Resubmit case" }));

    await waitFor(() =>
      expect(onResubmit).toHaveBeenCalledWith({
        performed_by_user_id: "reviewer-42",
        target_status: "queued_for_processing",
        comment: "Re-run extraction after reviewer correction.",
      }),
    );
  });

  it("records hold review as an explicit note", async () => {
    const onAddNote = vi.fn().mockResolvedValue(undefined);

    renderWithProviders(
      <ManualReviewFlowPanel
        caseStatus="manual_review_required"
        fields={[...fields]}
        actions={[]}
        onAddNote={onAddNote}
        onSubmitCorrections={vi.fn()}
        onResubmit={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("user-123"), { target: { value: "reviewer-42" } });
    fireEvent.change(screen.getByPlaceholderText("Explain the reviewer observation or reason for holding the case."), {
      target: { value: "Awaiting supervisor confirmation." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Hold review" }));

    await waitFor(() =>
      expect(onAddNote).toHaveBeenCalledWith({
        performed_by_user_id: "reviewer-42",
        comment: "[Hold] Awaiting supervisor confirmation.",
      }),
    );
  });
});

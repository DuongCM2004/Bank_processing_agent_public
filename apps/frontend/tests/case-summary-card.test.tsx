import { screen } from "@testing-library/react";

import { CaseSummaryCard } from "@/features/cases/components/CaseSummaryCard";
import { renderWithProviders } from "./render";

describe("CaseSummaryCard", () => {
  it("renders key case metadata for operations users", () => {
    renderWithProviders(
      <CaseSummaryCard
        caseDetail={{
          id: "case-123",
          case_reference: "CASE-123",
          case_type: "kyc_onboarding",
          status: "decision_ready",
          status_changed_at: "2026-04-15T10:00:00Z",
          current_queue: "document_ops",
          source_channel: "manual_upload",
          customer_reference: null,
          created_at: "2026-04-15T08:00:00Z",
          updated_at: "2026-04-15T10:30:00Z",
          submitted_by_user: null,
          metadata: {},
          documents: [],
          ocr_results: [],
          extraction_results: [],
          validation: {
            case_id: "case-123",
            validation_findings: [],
            risk_findings: [],
            compliance_findings: [],
            has_blocking_findings: false,
          },
          decisions: [],
          manual_review_actions: [],
          audit_events: [],
          closed_at: null,
        }}
      />,
    );

    expect(screen.getByText("Case summary")).toBeInTheDocument();
    expect(screen.getByText("CASE-123")).toBeInTheDocument();
    expect(screen.getByText("document ops")).toBeInTheDocument();
  });
});

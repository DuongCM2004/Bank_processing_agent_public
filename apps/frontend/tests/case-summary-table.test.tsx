import { screen } from "@testing-library/react";

import type { CaseSummary } from "@/api/contracts";
import { CaseSummaryTable } from "@/features/cases/components/CaseSummaryTable";
import { renderWithProviders } from "./render";

const caseItem: CaseSummary = {
  id: "d5ef2331-a7cb-4cbb-af18-99af3237df70",
  case_reference: "CASE-12345",
  case_type: "kyc_onboarding",
  status: "manual_review_required",
  status_changed_at: "2026-04-15T12:00:00Z",
  current_queue: "document_ops",
  source_channel: "manual_upload",
  customer_reference: "CUST-001",
  document_count: 3,
  created_at: "2026-04-15T10:00:00Z",
  updated_at: "2026-04-15T12:30:00Z",
};

describe("CaseSummaryTable", () => {
  it("shows the required ops columns and detail link", () => {
    renderWithProviders(<CaseSummaryTable cases={[caseItem]} />);

    expect(screen.getByText("Case ID")).toBeInTheDocument();
    expect(screen.getByText("Latest update")).toBeInTheDocument();
    expect(screen.getByText("Manual review")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "CASE-12345" })).toHaveAttribute("href", "/cases/d5ef2331-a7cb-4cbb-af18-99af3237df70");
    expect(screen.getByText("required")).toBeInTheDocument();
  });
});

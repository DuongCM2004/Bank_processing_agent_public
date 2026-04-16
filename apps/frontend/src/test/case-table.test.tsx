import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CaseTable } from "@/features/case-list/components/CaseTable";
import { renderWithProviders } from "@/test/render";
import type { CaseSummary } from "@/types/api";

const caseItem: CaseSummary = {
  id: "case-1",
  case_reference: "CASE-2026-001",
  case_type: "loan_application",
  status: "manual_review_required",
  status_changed_at: "2026-04-16T10:00:00Z",
  current_queue: "manual_review",
  source_channel: "branch",
  customer_reference: "CUST-1",
  document_count: 3,
  created_at: "2026-04-16T09:00:00Z",
  updated_at: "2026-04-16T10:00:00Z",
};

describe("CaseTable", () => {
  it("renders case metadata and manual review status", () => {
    renderWithProviders(<CaseTable cases={[caseItem]} />);

    expect(screen.getByRole("link", { name: "CASE-2026-001" })).toHaveAttribute("href", "/cases/case-1");
    expect(screen.getByText("manual_review")).toBeInTheDocument();
    expect(screen.getByText("Required")).toBeInTheDocument();
  });
});

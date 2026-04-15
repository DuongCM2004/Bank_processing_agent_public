import { screen } from "@testing-library/react";

import { CaseStatusBadge } from "@/features/cases/components/CaseStatusBadge";
import { renderWithProviders } from "./render";

describe("CaseStatusBadge", () => {
  it("renders status labels in a readable format", () => {
    renderWithProviders(<CaseStatusBadge status="manual_review_required" />);

    expect(screen.getByText("manual review required")).toBeInTheDocument();
  });
});

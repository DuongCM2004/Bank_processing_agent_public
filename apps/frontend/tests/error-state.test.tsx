import { screen } from "@testing-library/react";

import { ErrorState } from "@/components/ui/ErrorState";
import { renderWithProviders } from "./render";

describe("ErrorState", () => {
  it("renders the supplied message", () => {
    renderWithProviders(<ErrorState message="Backend unavailable." />);

    expect(screen.getByText("Backend unavailable.")).toBeInTheDocument();
  });
});

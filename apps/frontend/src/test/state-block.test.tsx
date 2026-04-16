import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StateBlock } from "@/components/ui/StateBlock";
import { renderWithProviders } from "@/test/render";

describe("StateBlock", () => {
  it("renders errors as alerts", () => {
    renderWithProviders(<StateBlock state="error" title="Failed" message="Backend unavailable." />);

    expect(screen.getByRole("alert")).toHaveTextContent("Failed");
    expect(screen.getByText("Backend unavailable.")).toBeInTheDocument();
  });
});

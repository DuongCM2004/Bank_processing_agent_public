import type { PropsWithChildren, ReactElement } from "react";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { AppProviders } from "@/app/providers";

function TestProviders({ children }: PropsWithChildren) {
  return (
    <AppProviders>
      <MemoryRouter>{children}</MemoryRouter>
    </AppProviders>
  );
}

export function renderWithProviders(ui: ReactElement) {
  return render(ui, { wrapper: TestProviders });
}

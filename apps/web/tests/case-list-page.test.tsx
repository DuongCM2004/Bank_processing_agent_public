import { screen } from "@testing-library/react";
import { vi } from "vitest";

import { CaseListPage } from "@/pages/cases/CaseListPage";
import { buildCaseListResponse, buildCaseSummary, buildErrorQueryState, buildLoadingQueryState, buildQueryState } from "./mock-api";
import { renderWithProviders } from "./render";

const refetch = vi.fn();
const useCasesQueryMock = vi.fn();
const createCaseMutateAsync = vi.fn();

vi.mock("@/features/cases/hooks", () => ({
  useCasesQuery: (...args: unknown[]) => useCasesQueryMock(...args),
  useCreateCaseMutation: () => ({
    mutateAsync: createCaseMutateAsync,
    isPending: false,
  }),
}));

describe("CaseListPage", () => {
  beforeEach(() => {
    refetch.mockReset();
    useCasesQueryMock.mockReset();
    createCaseMutateAsync.mockReset();
    useCasesQueryMock.mockReturnValue(
      buildQueryState({
        data: buildCaseListResponse({
          items: [
            buildCaseSummary(),
            buildCaseSummary({
              id: "22222222-2222-2222-2222-222222222222",
              case_reference: "CASE-BBB",
              case_type: "kyc_refresh",
              status: "approved",
              status_changed_at: "2026-04-15T09:00:00Z",
              document_count: 1,
              created_at: "2026-04-15T07:00:00Z",
              updated_at: "2026-04-15T09:15:00Z",
            }),
          ],
          total: 21,
        }),
        refetch,
      }),
    );
  });

  it("renders cases and local search filtering", async () => {
    const { user } = renderWithProviders(<CaseListPage />);

    expect(screen.getByRole("link", { name: "CASE-AAA" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "CASE-BBB" })).toBeInTheDocument();

    await user.type(screen.getByPlaceholderText("Search by case reference or UUID"), "BBB");

    expect(screen.queryByRole("link", { name: "CASE-AAA" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "CASE-BBB" })).toBeInTheDocument();
  });

  it("passes backend filter state and supports pagination changes", async () => {
    const { user } = renderWithProviders(<CaseListPage />);

    expect(useCasesQueryMock).toHaveBeenCalledWith({ limit: 10, offset: 0, status: undefined });

    await user.click(screen.getByRole("checkbox", { name: "Manual review only" }));
    expect(useCasesQueryMock).toHaveBeenLastCalledWith({ limit: 10, offset: 0, status: "manual_review_required" });

    await user.selectOptions(screen.getByDisplayValue("All statuses"), "approved");
    expect(useCasesQueryMock).toHaveBeenLastCalledWith({ limit: 10, offset: 0, status: "approved" });

    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(useCasesQueryMock).toHaveBeenLastCalledWith({ limit: 10, offset: 10, status: "approved" });
  });

  it("renders a loading state while the queue is being fetched", () => {
    useCasesQueryMock.mockReturnValue(buildLoadingQueryState(refetch));

    renderWithProviders(<CaseListPage />);

    expect(screen.getByText("Loading data...")).toBeInTheDocument();
  });

  it("renders an error state and retries the query", async () => {
    useCasesQueryMock.mockReturnValue(buildErrorQueryState(refetch));

    const { user } = renderWithProviders(<CaseListPage />);

    expect(screen.getByText("Case list could not be loaded.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Retry" }));

    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it("renders an empty state when no rows are returned", () => {
    useCasesQueryMock.mockReturnValue(buildQueryState({ data: buildCaseListResponse({ items: [], total: 0 }), refetch }));

    renderWithProviders(<CaseListPage />);

    expect(screen.getByText("No cases found")).toBeInTheDocument();
  });
});

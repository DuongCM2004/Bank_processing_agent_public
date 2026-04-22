import { screen } from "@testing-library/react";
import { vi } from "vitest";

import { CaseDetailPage } from "@/pages/cases/CaseDetailPage";
import { buildCaseWorkspace, buildErrorQueryState, buildLoadingQueryState, buildQueryState } from "./mock-api";
import { renderWithProviders } from "./render";

const refetch = vi.fn();
const useCaseWorkspaceQueryMock = vi.fn();
const transitionMutateAsync = vi.fn();
const uploadMutateAsync = vi.fn();
const queueMutateAsync = vi.fn();
const decisionMutateAsync = vi.fn();
const addNoteMutateAsync = vi.fn();
const submitCorrectionsMutateAsync = vi.fn();
const resubmitMutateAsync = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");

  return {
    ...actual,
    useParams: () => ({ caseId: "case-123" }),
  };
});

vi.mock("@/features/cases/hooks", () => ({
  useCaseWorkspaceQuery: (...args: unknown[]) => useCaseWorkspaceQueryMock(...args),
  useTransitionCaseStatusMutation: () => ({
    mutateAsync: transitionMutateAsync,
    isPending: false,
  }),
  useUploadCaseDocumentMutation: () => ({
    mutateAsync: uploadMutateAsync,
    isPending: false,
  }),
  useQueueCaseProcessingMutation: () => ({
    mutateAsync: queueMutateAsync,
    isPending: false,
  }),
  useCreateDecisionMutation: () => ({
    mutateAsync: decisionMutateAsync,
    isPending: false,
  }),
}));

vi.mock("@/features/review/hooks", () => ({
  useAddManualReviewNoteMutation: () => ({
    mutateAsync: addNoteMutateAsync,
    isPending: false,
  }),
  useSubmitManualCorrectionsMutation: () => ({
    mutateAsync: submitCorrectionsMutateAsync,
    isPending: false,
  }),
  useResubmitManualReviewCaseMutation: () => ({
    mutateAsync: resubmitMutateAsync,
    isPending: false,
  }),
}));

describe("CaseDetailPage", () => {
  beforeEach(() => {
    refetch.mockReset();
    useCaseWorkspaceQueryMock.mockReset();
    transitionMutateAsync.mockReset();
    uploadMutateAsync.mockReset();
    queueMutateAsync.mockReset();
    decisionMutateAsync.mockReset();
    addNoteMutateAsync.mockReset();
    submitCorrectionsMutateAsync.mockReset();
    resubmitMutateAsync.mockReset();
    useCaseWorkspaceQueryMock.mockReturnValue(buildQueryState({ data: buildCaseWorkspace(), refetch }));
  });

  it("renders the detail workspace sections", () => {
    renderWithProviders(<CaseDetailPage />);

    expect(useCaseWorkspaceQueryMock).toHaveBeenCalledWith("case-123");
    expect(screen.getByText("Case summary")).toBeInTheDocument();
    expect(screen.getByText("Document intake")).toBeInTheDocument();
    expect(screen.getByText("Stored documents")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Upload document" })).toBeInTheDocument();
    expect(screen.getByText("Document viewer")).toBeInTheDocument();
    expect(screen.getByText("Extraction summary")).toBeInTheDocument();
    expect(screen.getByText("Extraction review")).toBeInTheDocument();
    expect(screen.getByText("Validation findings")).toBeInTheDocument();
    expect(screen.getByText("Manual review")).toBeInTheDocument();
    expect(screen.getByText("Decision summary")).toBeInTheDocument();
    expect(screen.getByText("Audit history preview")).toBeInTheDocument();
  });

  it("renders a loading state while the case workspace is being fetched", () => {
    useCaseWorkspaceQueryMock.mockReturnValue(buildLoadingQueryState(refetch));

    renderWithProviders(<CaseDetailPage />);

    expect(screen.getByText("Loading data...")).toBeInTheDocument();
  });

  it("renders an error state and retries the case workspace query", async () => {
    useCaseWorkspaceQueryMock.mockReturnValue(buildErrorQueryState(refetch));

    const { user } = renderWithProviders(<CaseDetailPage />);

    expect(screen.getByText("The case detail could not be loaded.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Retry" }));

    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it("renders the empty state when no case data is returned", () => {
    useCaseWorkspaceQueryMock.mockReturnValue(buildQueryState({ data: undefined, refetch }));

    renderWithProviders(<CaseDetailPage />);

    expect(screen.getByText("Case not found")).toBeInTheDocument();
  });
});

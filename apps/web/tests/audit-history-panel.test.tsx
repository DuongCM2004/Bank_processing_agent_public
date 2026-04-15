import { screen, within } from "@testing-library/react";

import { AuditHistoryPanel } from "@/features/audit/components/AuditHistoryPanel";
import { renderWithProviders } from "./render";

describe("AuditHistoryPanel", () => {
  it("renders a scan-friendly chronological timeline with actor and metadata context", () => {
    renderWithProviders(
      <AuditHistoryPanel
        totalEvents={3}
        events={[
          {
            id: "audit-1",
            case_id: "case-123",
            actor_user_id: "reviewer-7",
            actor_type: "user",
            actor_identifier: "reviewer-7",
            event_type: "manual_review_action_recorded",
            summary: "Reviewer placed the case on hold.",
            resource_type: "manual_review_action",
            resource_id: "mra-1",
            occurred_at: "2026-04-15T10:30:00Z",
            metadata: { hold_reason: "awaiting_supervisor" },
            evidence_refs: [],
            created_at: "2026-04-15T10:30:00Z",
            updated_at: "2026-04-15T10:30:00Z",
          },
          {
            id: "audit-2",
            case_id: "case-123",
            actor_user_id: null,
            actor_type: "system",
            actor_identifier: "workflow-engine",
            event_type: "status_changed",
            summary: "Case status moved to manual review.",
            resource_type: "case",
            resource_id: "case-123",
            occurred_at: "2026-04-15T09:30:00Z",
            metadata: {},
            evidence_refs: [],
            created_at: "2026-04-15T09:30:00Z",
            updated_at: "2026-04-15T09:30:00Z",
          },
          {
            id: "audit-3",
            case_id: "case-123",
            actor_user_id: null,
            actor_type: "service",
            actor_identifier: "ocr-worker",
            event_type: "ocr_completed",
            summary: "OCR finished for the uploaded document.",
            resource_type: "ocr_result",
            resource_id: "ocr-1",
            occurred_at: "2026-04-15T10:00:00Z",
            metadata: { page_count: 2 },
            evidence_refs: [],
            created_at: "2026-04-15T10:00:00Z",
            updated_at: "2026-04-15T10:00:00Z",
          },
        ]}
      />,
    );

    expect(screen.getByText("Audit history")).toBeInTheDocument();
    expect(screen.getByText("3 total audit events recorded")).toBeInTheDocument();
    expect(screen.getByText("human")).toBeInTheDocument();
    expect(screen.getByText("system")).toBeInTheDocument();
    expect(screen.getByText("service")).toBeInTheDocument();
    expect(screen.getAllByText("Metadata preview")).toHaveLength(2);

    const articles = screen.getAllByRole("article");
    expect(within(articles[0]).getByText("Reviewer placed the case on hold.")).toBeInTheDocument();
    expect(within(articles[1]).getByText("OCR finished for the uploaded document.")).toBeInTheDocument();
    expect(within(articles[2]).getByText("Case status moved to manual review.")).toBeInTheDocument();
  });

  it("renders an empty state when there are no audit events", () => {
    renderWithProviders(<AuditHistoryPanel events={[]} emptyMessage="No audit activity available." />);

    expect(screen.getByText("No audit activity available.")).toBeInTheDocument();
  });
});

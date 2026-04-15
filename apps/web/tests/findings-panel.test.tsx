import { screen } from "@testing-library/react";

import { FindingsPanel } from "@/features/review/components/FindingsPanel";
import { renderWithProviders } from "./render";

describe("FindingsPanel", () => {
  it("groups findings and makes blocking vs non-blocking issues obvious", () => {
    renderWithProviders(
      <FindingsPanel
        validationFindings={[
          {
            id: "vf-1",
            case_id: "case-123",
            document_id: "doc-1",
            extraction_result_id: "ext-1",
            rule_code: "document_number_check",
            field_name: "document_number",
            message: "Document number does not match the expected pattern.",
            severity: "critical",
            status: "open",
            resolution_note: null,
            evidence_refs: [],
            created_at: "2026-04-15T10:00:00Z",
            updated_at: "2026-04-15T10:00:00Z",
          },
          {
            id: "vf-2",
            case_id: "case-123",
            document_id: "doc-1",
            extraction_result_id: "ext-1",
            rule_code: "name_format_check",
            field_name: "full_name",
            message: "Name formatting requires a reviewer confirmation.",
            severity: "warning",
            status: "open",
            resolution_note: null,
            evidence_refs: [],
            created_at: "2026-04-15T10:00:00Z",
            updated_at: "2026-04-15T10:00:00Z",
          },
        ]}
        riskFindings={[
          {
            id: "rf-1",
            case_id: "case-123",
            document_id: "doc-1",
            extraction_result_id: "ext-1",
            risk_code: "sanctions_watchlist",
            message: "Potential watchlist similarity detected.",
            risk_level: "high",
            status: "open",
            risk_score: 0.88,
            evidence_refs: [
              {
                document_id: "doc-1",
                page_number: 1,
                text_anchor: "Jane D",
                extracted_value: "Jane D",
                metadata: { field_name: "full_name" },
              },
            ],
            created_at: "2026-04-15T10:00:00Z",
            updated_at: "2026-04-15T10:00:00Z",
          },
        ]}
        complianceFindings={[
          {
            id: "cf-1",
            case_id: "case-123",
            document_id: "doc-1",
            extraction_result_id: "ext-1",
            policy_code: "kyc_document_complete",
            regulation_reference: "KYC-4.2",
            message: "Required documentation set has been completed.",
            severity: "info",
            status: "resolved",
            evidence_refs: [],
            created_at: "2026-04-15T10:00:00Z",
            updated_at: "2026-04-15T10:00:00Z",
          },
        ]}
      />,
    );

    expect(screen.getByText("Validation findings")).toBeInTheDocument();
    expect(screen.getByText("Blocking")).toBeInTheDocument();
    expect(screen.getByText("Warnings")).toBeInTheDocument();
    expect(screen.getByText("Passed or closed")).toBeInTheDocument();
    expect(screen.getByText("document number check")).toBeInTheDocument();
    expect(screen.getByText("sanctions watchlist")).toBeInTheDocument();
    expect(screen.getByText("kyc document complete")).toBeInTheDocument();
    expect(screen.getByText("Linked field: document number")).toBeInTheDocument();
    expect(screen.getByText("Linked field: full name")).toBeInTheDocument();
    expect(screen.getAllByText("blocking")).not.toHaveLength(0);
    expect(screen.getByText("Status: resolved | KYC-4.2")).toBeInTheDocument();
  });

  it("renders empty grouped sections when there are no findings", () => {
    renderWithProviders(
      <FindingsPanel validationFindings={[]} riskFindings={[]} complianceFindings={[]} />,
    );

    expect(screen.getAllByText("No findings recorded.")).toHaveLength(3);
  });
});

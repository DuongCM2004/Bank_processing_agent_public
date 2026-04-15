import { fireEvent, screen } from "@testing-library/react";
import { vi } from "vitest";

import { DocumentViewerShell } from "@/features/documents/components/DocumentViewerShell";
import { renderWithProviders } from "./render";

const documents = [
  {
    id: "doc-1",
    case_id: "case-123",
    filename: "passport.pdf",
    document_type: "passport",
    mime_type: "application/pdf",
    source_channel: "manual_upload",
    storage_key: "cases/case-123/passport.pdf",
    sha256_digest: "a".repeat(64),
    file_size_bytes: 2048,
    uploaded_at: "2026-04-15T08:00:00Z",
    status: "review_required" as const,
    status_changed_at: "2026-04-15T10:00:00Z",
    page_count: 2,
    metadata: {},
    created_at: "2026-04-15T08:00:00Z",
    updated_at: "2026-04-15T10:00:00Z",
  },
  {
    id: "doc-2",
    case_id: "case-123",
    filename: "bank-statement.png",
    document_type: "bank_statement",
    mime_type: "image/png",
    source_channel: "manual_upload",
    storage_key: "cases/case-123/bank-statement.png",
    sha256_digest: "b".repeat(64),
    file_size_bytes: 1024,
    uploaded_at: "2026-04-15T09:00:00Z",
    status: "extraction_completed" as const,
    status_changed_at: "2026-04-15T11:00:00Z",
    page_count: 1,
    metadata: {},
    created_at: "2026-04-15T09:00:00Z",
    updated_at: "2026-04-15T11:00:00Z",
  },
];

describe("DocumentViewerShell", () => {
  it("renders the selected document metadata and switches documents", () => {
    const onSelectedDocumentChange = vi.fn();

    renderWithProviders(
      <DocumentViewerShell
        documents={documents}
        previewMode="pdf"
        previewUrl="/secure-preview/doc-1"
        evidenceAnchors={[
          {
            id: "anchor-1",
            documentId: "doc-1",
            label: "Document number",
            pageNumber: 1,
            extractedValue: "ABC123",
          },
          {
            id: "anchor-2",
            documentId: "doc-2",
            label: "Account holder",
            pageNumber: 1,
            extractedValue: "Jane Doe",
          },
        ]}
        onSelectedDocumentChange={onSelectedDocumentChange}
      />,
    );

    expect(screen.getByText("PDF embed placeholder")).toBeInTheDocument();
    expect(screen.getAllByText("passport.pdf")).not.toHaveLength(0);
    expect(screen.getByText("Preview source: /secure-preview/doc-1")).toBeInTheDocument();
    expect(screen.getByText("Document ID")).toBeInTheDocument();
    expect(screen.getByText("2.0 KB")).toBeInTheDocument();
    expect(screen.getByText("Document number")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /bank-statement\.png/i }));

    expect(onSelectedDocumentChange).toHaveBeenCalledWith("doc-2");
    expect(screen.getAllByText("bank-statement.png")).not.toHaveLength(0);
    expect(screen.getByText("Account holder")).toBeInTheDocument();
    expect(screen.getByText("1.0 KB")).toBeInTheDocument();
  });

  it("renders an empty state when no documents are available", () => {
    renderWithProviders(<DocumentViewerShell documents={[]} />);

    expect(screen.getByText("No documents are available for preview in this case.")).toBeInTheDocument();
  });
});

import { Panel } from "@/components/ui/Panel";
import { LinkedDocuments } from "@/features/case-detail/components/LinkedDocuments";
import type { DocumentUploadMetadata } from "@/types/api";

export interface EvidenceAnchor {
  id: string;
  documentId: string;
  label: string;
  pageNumber?: number | null;
  extractedValue?: string | null;
}

interface DocumentViewerShellProps {
  documents: DocumentUploadMetadata[];
  selectedDocumentId: string | null;
  evidenceAnchors: EvidenceAnchor[];
  onSelectDocument: (documentId: string) => void;
}

export function DocumentViewerShell({
  documents,
  selectedDocumentId,
  evidenceAnchors,
  onSelectDocument,
}: DocumentViewerShellProps) {
  const selectedDocument = documents.find((document) => document.id === selectedDocumentId) ?? documents[0] ?? null;
  const selectedAnchors = selectedDocument
    ? evidenceAnchors.filter((anchor) => anchor.documentId === selectedDocument.id).slice(0, 6)
    : [];

  return (
    <Panel title="Document viewer" description="Document shell with metadata, preview placeholder, and evidence anchor compatibility.">
      <div className="grid gap-5 lg:grid-cols-[280px_minmax(0,1fr)]">
        <LinkedDocuments documents={documents} selectedDocumentId={selectedDocument?.id ?? null} onSelectDocument={onSelectDocument} />
        <div className="min-h-[420px] rounded-lg border border-dashed border-line bg-surface p-4">
          {selectedDocument ? (
            <div className="flex h-full flex-col">
              <div className="flex flex-wrap items-start justify-between gap-3 border-b border-line pb-3">
                <div>
                  <p className="font-semibold text-ink">{selectedDocument.filename}</p>
                  <p className="mt-1 text-sm text-muted">
                    {selectedDocument.mime_type} | {selectedDocument.page_count ?? "N/A"} pages
                  </p>
                </div>
                <p className="rounded-md bg-panel px-2 py-1 text-xs font-semibold text-muted">Preview placeholder</p>
              </div>
              <div className="grid flex-1 place-items-center py-10 text-center">
                <div>
                  <p className="text-sm font-semibold text-ink">Document preview surface</p>
                  <p className="mt-2 max-w-md text-sm leading-6 text-muted">
                    Backend file rendering and evidence highlights can attach here without changing the surrounding review layout.
                  </p>
                </div>
              </div>
              <div className="border-t border-line pt-3">
                <p className="text-xs font-bold uppercase tracking-wider text-muted">Evidence anchors</p>
                {selectedAnchors.length === 0 ? (
                  <p className="mt-2 text-sm text-muted">No evidence anchors were supplied for this document.</p>
                ) : (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {selectedAnchors.map((anchor) => (
                      <span key={anchor.id} className="rounded-md border border-blue/20 bg-blueSoft px-2 py-1 text-xs font-semibold text-blue">
                        {anchor.label}
                        {anchor.pageNumber ? ` p.${anchor.pageNumber}` : ""}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted">No document selected.</p>
          )}
        </div>
      </div>
    </Panel>
  );
}

import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import type { DocumentUploadMetadata } from "@/api/contracts";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { documentStatusTones } from "@/features/documents/status";
import { cn } from "@/lib/cn";

export interface DocumentViewerEvidenceAnchor {
  id: string;
  documentId: string;
  label: string;
  pageNumber?: number | null;
  extractedValue?: string | null;
  metadata?: Record<string, string>;
}

export interface DocumentViewerShellProps {
  documents: DocumentUploadMetadata[];
  selectedDocumentId?: string;
  onSelectedDocumentChange?: (documentId: string) => void;
  previewMode?: "placeholder" | "image" | "pdf";
  previewUrl?: string | null;
  previewSlot?: ReactNode;
  metadataSlot?: ReactNode;
  evidenceAnchors?: DocumentViewerEvidenceAnchor[];
  className?: string;
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString();
}

function formatPreviewMode(mode: DocumentViewerShellProps["previewMode"]) {
  if (mode === "pdf") {
    return "PDF embed placeholder";
  }
  if (mode === "image") {
    return "Image preview placeholder";
  }
  return "Document preview placeholder";
}

function formatFileSize(value?: number | null) {
  if (!value || value <= 0) {
    return "Unknown";
  }

  if (value < 1024) {
    return `${value} B`;
  }

  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }

  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function DocumentViewerShell({
  documents,
  selectedDocumentId,
  onSelectedDocumentChange,
  previewMode = "placeholder",
  previewUrl,
  previewSlot,
  metadataSlot,
  evidenceAnchors = [],
  className,
}: DocumentViewerShellProps) {
  const [internalSelectedDocumentId, setInternalSelectedDocumentId] = useState<string | undefined>(
    selectedDocumentId ?? documents[0]?.id,
  );

  useEffect(() => {
    if (selectedDocumentId !== undefined) {
      setInternalSelectedDocumentId(selectedDocumentId);
      return;
    }

    if (!internalSelectedDocumentId && documents.length > 0) {
      setInternalSelectedDocumentId(documents[0].id);
    }
  }, [documents, internalSelectedDocumentId, selectedDocumentId]);

  const activeDocumentId = selectedDocumentId ?? internalSelectedDocumentId;
  const selectedDocument = documents.find((document) => document.id === activeDocumentId) ?? documents[0] ?? null;
  const selectedDocumentAnchors = evidenceAnchors.filter((anchor) => anchor.documentId === selectedDocument?.id);

  function handleSelectDocument(documentId: string) {
    if (selectedDocumentId === undefined) {
      setInternalSelectedDocumentId(documentId);
    }

    onSelectedDocumentChange?.(documentId);
  }

  return (
    <Card
      className={className}
      title="Document viewer"
      description="Selected document workspace with metadata, preview shell, and future evidence-overlay compatibility."
    >
      {documents.length === 0 || !selectedDocument ? (
        <div className="rounded-2xl border border-dashed border-line bg-mist px-6 py-10 text-sm text-slate">
          No documents are available for preview in this case.
        </div>
      ) : (
        <div className="grid gap-5 xl:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="space-y-3">
            <p className="eyebrow">Documents</p>
            {documents.map((document) => {
              const isActive = document.id === selectedDocument.id;

              return (
                <button
                  key={document.id}
                  type="button"
                  onClick={() => handleSelectDocument(document.id)}
                  className={cn(
                    "w-full rounded-2xl border px-4 py-4 text-left transition-colors",
                    isActive ? "border-accent bg-accentSoft/60" : "border-line bg-white hover:bg-mist",
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-ink">{document.filename}</p>
                      <p className="mt-1 text-xs text-slate">{document.document_type}</p>
                    </div>
                    <StatusBadge tone={documentStatusTones[document.status]}>{document.status}</StatusBadge>
                  </div>
                </button>
              );
            })}
          </aside>

          <div className="grid gap-5 2xl:grid-cols-[minmax(0,1.3fr)_360px]">
            <section className="space-y-4">
              <div
                className="flex min-h-[460px] items-center justify-center rounded-3xl border border-dashed border-line bg-mist p-6"
                data-evidence-ready="true"
              >
                {previewSlot ?? (
                  <div className="max-w-md text-center">
                    <p className="eyebrow">Preview area</p>
                    <h3 className="mt-3 text-xl font-semibold text-ink">{formatPreviewMode(previewMode)}</h3>
                    <p className="mt-2 text-sm font-medium text-ink">{selectedDocument.filename}</p>
                    <p className="mt-3 text-sm leading-6 text-slate">
                      Render the selected document here once secure PDF or image preview delivery is available. This container is reserved for
                      future OCR and extraction evidence overlays.
                    </p>
                    {previewUrl ? (
                      <p className="mt-3 break-all rounded-2xl bg-white/70 px-3 py-2 text-left font-mono text-xs text-slate">
                        Preview source: {previewUrl}
                      </p>
                    ) : null}
                  </div>
                )}
              </div>

              <div className="rounded-2xl border border-line bg-white p-4">
                <p className="eyebrow">Evidence overlay readiness</p>
                <p className="mt-2 text-sm text-slate">
                  {selectedDocumentAnchors.length} evidence anchors currently linked to the selected document. Overlay rendering is intentionally
                  deferred to a future enhancement.
                </p>
              </div>
            </section>

            <aside className="space-y-4">
              {metadataSlot ?? (
                <div className="rounded-2xl border border-line bg-white p-5">
                  <p className="eyebrow">Metadata</p>
                  <dl className="mt-4 space-y-3 text-sm">
                    <div>
                      <dt className="font-medium text-ink">Document ID</dt>
                      <dd className="mt-1 break-all font-mono text-xs text-slate">{selectedDocument.id}</dd>
                    </div>
                    <div>
                      <dt className="font-medium text-ink">Filename</dt>
                      <dd className="mt-1 text-slate">{selectedDocument.filename}</dd>
                    </div>
                    <div>
                      <dt className="font-medium text-ink">Document type</dt>
                      <dd className="mt-1 text-slate">{selectedDocument.document_type}</dd>
                    </div>
                    <div>
                      <dt className="font-medium text-ink">MIME type</dt>
                      <dd className="mt-1 text-slate">{selectedDocument.mime_type}</dd>
                    </div>
                    <div>
                      <dt className="font-medium text-ink">Size</dt>
                      <dd className="mt-1 text-slate">{formatFileSize(selectedDocument.file_size_bytes)}</dd>
                    </div>
                    <div>
                      <dt className="font-medium text-ink">Pages</dt>
                      <dd className="mt-1 text-slate">{selectedDocument.page_count ?? "Unknown"}</dd>
                    </div>
                    <div>
                      <dt className="font-medium text-ink">Uploaded</dt>
                      <dd className="mt-1 text-slate">{formatDateTime(selectedDocument.uploaded_at)}</dd>
                    </div>
                    <div>
                      <dt className="font-medium text-ink">Storage key</dt>
                      <dd className="mt-1 break-all font-mono text-xs text-slate">{selectedDocument.storage_key}</dd>
                    </div>
                    <div>
                      <dt className="font-medium text-ink">Digest</dt>
                      <dd className="mt-1 break-all font-mono text-xs text-slate">{selectedDocument.sha256_digest}</dd>
                    </div>
                  </dl>
                </div>
              )}

              <div className="rounded-2xl border border-line bg-white p-5">
                <p className="eyebrow">Evidence anchors</p>
                {selectedDocumentAnchors.length === 0 ? (
                  <p className="mt-3 text-sm text-slate">No evidence anchors attached to this document yet.</p>
                ) : (
                  <div className="mt-3 space-y-3">
                    {selectedDocumentAnchors.map((anchor) => (
                      <div key={anchor.id} className="rounded-xl bg-mist px-3 py-3" data-evidence-ready="true">
                        <p className="text-sm font-semibold text-ink">{anchor.label}</p>
                        <p className="mt-1 text-xs text-slate">
                          Page {anchor.pageNumber ?? "n/a"} {anchor.extractedValue ? `· ${anchor.extractedValue}` : ""}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </aside>
          </div>
        </div>
      )}
    </Card>
  );
}

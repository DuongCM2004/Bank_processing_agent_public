import { FormEvent, useState } from "react";

import type { DocumentUploadMetadata } from "@/api/contracts";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useUploadCaseDocumentMutation } from "@/features/cases/hooks";

interface DocumentManagementPanelProps {
  caseId: string;
  documents: DocumentUploadMetadata[];
}

const tones = {
  uploaded: "active",
  stored: "active",
  ocr_pending: "warning",
  ocr_completed: "active",
  extraction_completed: "success",
  review_required: "warning",
  failed: "danger",
  archived: "neutral",
} as const;

function parseJsonObject(value: string): Record<string, unknown> {
  if (value.trim().length === 0) {
    return {};
  }

  const parsed = JSON.parse(value) as unknown;
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error("Metadata must be a JSON object.");
  }

  return parsed as Record<string, unknown>;
}

function formatFileSize(value?: number | null) {
  if (!value || value <= 0) {
    return "Unknown size";
  }

  if (value < 1024) {
    return `${value} B`;
  }

  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }

  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function DocumentManagementPanel({ caseId, documents }: DocumentManagementPanelProps) {
  const uploadMutation = useUploadCaseDocumentMutation(caseId);
  const [actorId, setActorId] = useState("");
  const [documentType, setDocumentType] = useState("bank_statement");
  const [documentMetadata, setDocumentMetadata] = useState("{}");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFeedback(null);

    if (!selectedFile) {
      setFeedback("Choose a document file before uploading.");
      return;
    }

    try {
      await uploadMutation.mutateAsync({
        file: selectedFile,
        documentType: documentType.trim() || "document",
        documentMetadata: parseJsonObject(documentMetadata),
        actorId: actorId.trim() || null,
      });
      setSelectedFile(null);
      setFeedback("Document uploaded. The list will refresh automatically.");
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "Document could not be uploaded.");
    }
  }

  return (
    <Card
      title="Document intake"
      description="Upload documents to this case and review the records returned by the backend document list endpoint."
    >
      <div className="grid gap-5 xl:grid-cols-[minmax(320px,0.9fr)_minmax(0,1.1fr)]">
        <form onSubmit={handleUpload} className="rounded-2xl border border-line p-4">
          <p className="eyebrow">Upload document</p>
          <div className="mt-4 grid gap-3">
            <label className="space-y-2 text-sm text-slate">
              <span className="font-medium text-ink">File</span>
              <input
                type="file"
                onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink"
              />
            </label>
            <label className="space-y-2 text-sm text-slate">
              <span className="font-medium text-ink">Document type</span>
              <input
                value={documentType}
                onChange={(event) => setDocumentType(event.target.value)}
                maxLength={80}
                className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-accent"
              />
            </label>
            <label className="space-y-2 text-sm text-slate">
              <span className="font-medium text-ink">Actor ID</span>
              <input
                value={actorId}
                onChange={(event) => setActorId(event.target.value)}
                maxLength={128}
                placeholder="Optional"
                className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-accent"
              />
            </label>
            <label className="space-y-2 text-sm text-slate">
              <span className="font-medium text-ink">Metadata JSON</span>
              <textarea
                value={documentMetadata}
                onChange={(event) => setDocumentMetadata(event.target.value)}
                rows={4}
                className="w-full rounded-2xl border border-line bg-white px-3 py-3 font-mono text-xs text-ink outline-none transition focus:border-accent"
              />
            </label>
            <div className="flex flex-wrap items-center gap-3">
              <Button type="submit" disabled={uploadMutation.isPending}>
                Upload document
              </Button>
              {selectedFile ? <span className="text-sm text-slate">{selectedFile.name}</span> : null}
            </div>
            {feedback ? <p className="rounded-xl bg-mist px-3 py-2 text-sm text-slate">{feedback}</p> : null}
          </div>
        </form>

        <section className="rounded-2xl border border-line p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="eyebrow">Stored documents</p>
              <p className="mt-1 text-sm text-slate">{documents.length} document records linked to this case</p>
            </div>
            <StatusBadge tone={documents.length > 0 ? "active" : "neutral"}>{String(documents.length)}</StatusBadge>
          </div>

          {documents.length === 0 ? (
            <div className="mt-4 rounded-2xl border border-dashed border-line bg-mist px-4 py-8 text-sm text-slate">
              No documents have been uploaded for this case.
            </div>
          ) : (
            <div className="mt-4 space-y-3">
              {documents.map((document) => (
                <article key={document.id} className="rounded-2xl border border-line bg-white p-4">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div className="min-w-0">
                      <p className="font-semibold text-ink">{document.filename}</p>
                      <p className="mt-1 text-sm text-slate">
                        {document.document_type} | {document.mime_type} | {formatFileSize(document.file_size_bytes)}
                      </p>
                      <p className="mt-2 break-all font-mono text-xs text-slate">{document.id}</p>
                    </div>
                    <StatusBadge tone={tones[document.status]}>{document.status}</StatusBadge>
                  </div>
                  <dl className="mt-3 grid gap-3 text-xs text-slate md:grid-cols-2">
                    <div>
                      <dt className="font-medium text-ink">Uploaded</dt>
                      <dd>{new Date(document.uploaded_at).toLocaleString()}</dd>
                    </div>
                    <div>
                      <dt className="font-medium text-ink">SHA-256</dt>
                      <dd className="break-all font-mono">{document.sha256_digest}</dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </Card>
  );
}

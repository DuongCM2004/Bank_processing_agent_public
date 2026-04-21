import { ChangeEvent, DragEvent, FormEvent, useEffect, useRef, useState } from "react";

import type { DocumentUploadMetadata, IdentityDocumentExtraction } from "@/api/contracts";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useUploadCaseDocumentMutation } from "@/features/cases/hooks";
import { useUuidAuditEventsQuery } from "@/features/audit/hooks";
import { useDocumentExtractionQuery, useDocumentStatusQuery, useReviewDocumentMutation } from "@/features/documents/hooks";
import { documentStatusTones } from "@/features/documents/status";

interface DocumentManagementPanelProps {
  caseId: string;
  documents: DocumentUploadMetadata[];
  initialSelectedFile?: File | null;
  onInitialSelectedFileConsumed?: () => void;
}

const identityFieldNames = [
  "document_type",
  "full_name",
  "first_name",
  "last_name",
  "id_number",
  "document_number",
  "date_of_birth",
  "sex",
  "gender",
  "nationality",
  "place_of_birth",
  "issue_date",
  "expiry_date",
  "issuing_authority",
  "address",
  "raw_full_text",
] as const;

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

function toReviewPayload(values: Record<string, string>): IdentityDocumentExtraction {
  const valueFor = (fieldName: (typeof identityFieldNames)[number]) => {
    const value = values[fieldName]?.trim();
    return value ? value : null;
  };

  return {
    document_type: valueFor("document_type"),
    full_name: valueFor("full_name"),
    first_name: valueFor("first_name"),
    last_name: valueFor("last_name"),
    id_number: valueFor("id_number"),
    document_number: valueFor("document_number"),
    date_of_birth: valueFor("date_of_birth"),
    sex: valueFor("sex"),
    gender: valueFor("gender"),
    nationality: valueFor("nationality"),
    place_of_birth: valueFor("place_of_birth"),
    issue_date: valueFor("issue_date"),
    expiry_date: valueFor("expiry_date"),
    issuing_authority: valueFor("issuing_authority"),
    address: valueFor("address"),
    raw_full_text: valueFor("raw_full_text"),
  };
}

function formatFieldName(value: string) {
  return value.split("_").join(" ");
}

export function DocumentManagementPanel({
  caseId,
  documents,
  initialSelectedFile,
  onInitialSelectedFileConsumed,
}: DocumentManagementPanelProps) {
  const uploadMutation = useUploadCaseDocumentMutation(caseId);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [actorId, setActorId] = useState("");
  const [documentType, setDocumentType] = useState("bank_statement");
  const [documentMetadata, setDocumentMetadata] = useState("{}");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | undefined>(documents[0]?.id);
  const [reviewComment, setReviewComment] = useState("");
  const [reviewDraft, setReviewDraft] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<string | null>(null);
  const selectedDocument = documents.find((document) => document.id === selectedDocumentId);
  const documentStatusQuery = useDocumentStatusQuery(selectedDocumentId);
  const extractionQuery = useDocumentExtractionQuery(selectedDocumentId);
  const auditQuery = useUuidAuditEventsQuery({ entityUuid: selectedDocumentId });
  const reviewMutation = useReviewDocumentMutation(caseId, selectedDocumentId);

  useEffect(() => {
    if (initialSelectedFile) {
      setSelectedFile(initialSelectedFile);
      setFeedback(null);
    }
  }, [initialSelectedFile]);

  useEffect(() => {
    if (!selectedDocumentId && documents.length > 0) {
      setSelectedDocumentId(documents[0].id);
      return;
    }

    if (selectedDocumentId && !documents.some((document) => document.id === selectedDocumentId)) {
      setSelectedDocumentId(documents[0]?.id);
    }
  }, [documents, selectedDocumentId]);

  useEffect(() => {
    if (!extractionQuery.data?.fields) {
      setReviewDraft({});
      return;
    }

    setReviewDraft(
      Object.fromEntries(
        extractionQuery.data.fields.map((field) => [field.field_name, field.reviewed_value ?? field.extracted_value ?? ""]),
      ),
    );
  }, [extractionQuery.data?.fields]);

  function handleChooseFile() {
    fileInputRef.current?.click();
  }

  function handleSelectedFile(file: File | null) {
    setSelectedFile(file);
    setFeedback(null);
  }

  function handleFileInputChange(event: ChangeEvent<HTMLInputElement>) {
    handleSelectedFile(event.target.files?.[0] ?? null);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    handleSelectedFile(event.dataTransfer.files?.[0] ?? null);
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
  }

  function handleClearFile() {
    setSelectedFile(null);
    onInitialSelectedFileConsumed?.();
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

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
      handleClearFile();
      setFeedback("Document uploaded. The list will refresh automatically.");
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "Document could not be uploaded.");
    }
  }

  async function submitReview(action: "edit" | "approve" | "reject") {
    setFeedback(null);
    if (!selectedDocumentId) {
      setFeedback("Select a document before submitting review.");
      return;
    }

    try {
      await reviewMutation.mutateAsync({
        action,
        reviewer_id: actorId.trim() || "reviewer-ui",
        reviewed_payload: action === "reject" ? null : toReviewPayload(reviewDraft),
        comment: reviewComment.trim() || null,
      });
      setReviewComment("");
      setFeedback(action === "reject" ? "Document rejected." : "Manual review update saved.");
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "Manual review update failed.");
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
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              className="rounded-2xl border border-dashed border-line bg-mist p-4 transition hover:border-accent"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.txt,.csv,.doc,.docx,.xls,.xlsx,application/pdf,image/*,text/plain,text/csv,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                onChange={handleFileInputChange}
                className="sr-only"
              />
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-semibold text-ink">Local computer file</p>
                  <p className="mt-1 text-sm text-slate">Choose a PDF, image, spreadsheet, text file, or Word document.</p>
                </div>
                <Button type="button" variant="secondary" onClick={handleChooseFile}>
                  Browse local computer
                </Button>
              </div>
              {selectedFile ? (
                <div className="mt-4 rounded-xl border border-line bg-white p-3">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-ink">{selectedFile.name}</p>
                      <p className="mt-1 text-sm text-slate">
                        {selectedFile.type || "Unknown type"} | {formatFileSize(selectedFile.size)}
                      </p>
                    </div>
                    <Button type="button" variant="ghost" onClick={handleClearFile}>
                      Remove
                    </Button>
                  </div>
                </div>
              ) : (
                <p className="mt-4 text-sm text-slate">No local file selected.</p>
              )}
            </div>
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
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge tone={documentStatusTones[document.status]}>{document.status}</StatusBadge>
                      <Button type="button" variant="secondary" onClick={() => setSelectedDocumentId(document.id)}>
                        Review
                      </Button>
                    </div>
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

          {selectedDocument ? (
            <div className="mt-5 rounded-2xl border border-line bg-white p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="eyebrow">Extraction review</p>
                  <p className="mt-1 break-all text-xs text-slate">{selectedDocument.id}</p>
                </div>
                <StatusBadge tone={documentStatusTones[documentStatusQuery.data?.status ?? selectedDocument.status]}>
                  {documentStatusQuery.data?.status ?? selectedDocument.status}
                </StatusBadge>
              </div>

              {extractionQuery.isError ? (
                <p className="mt-4 rounded-xl bg-dangerSoft px-3 py-2 text-sm text-danger">Extraction data could not be loaded.</p>
              ) : extractionQuery.isLoading ? (
                <p className="mt-4 rounded-xl bg-mist px-3 py-2 text-sm text-slate">Loading extraction fields...</p>
              ) : (
                <div className="mt-4 overflow-x-auto">
                  <table className="min-w-full divide-y divide-line text-sm">
                    <thead>
                      <tr className="text-left text-xs uppercase text-slate">
                        <th className="py-2 pr-3 font-semibold">Field</th>
                        <th className="px-3 py-2 font-semibold">Extracted</th>
                        <th className="py-2 pl-3 font-semibold">Reviewed</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line">
                      {(extractionQuery.data?.fields ?? []).map((field) => (
                        <tr key={field.field_name}>
                          <td className="py-2 pr-3 font-medium text-ink">{formatFieldName(field.field_name)}</td>
                          <td className="max-w-[220px] px-3 py-2 text-slate">{field.extracted_value ?? "null"}</td>
                          <td className="py-2 pl-3">
                            <input
                              value={reviewDraft[field.field_name] ?? ""}
                              onChange={(event) => setReviewDraft((current) => ({ ...current, [field.field_name]: event.target.value }))}
                              className="w-full min-w-[180px] rounded-lg border border-line bg-white px-2 py-1.5 text-sm text-ink outline-none focus:border-accent"
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <label className="mt-4 block space-y-2 text-sm text-slate">
                <span className="font-medium text-ink">Review comment</span>
                <textarea
                  value={reviewComment}
                  onChange={(event) => setReviewComment(event.target.value)}
                  rows={3}
                  className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none focus:border-accent"
                />
              </label>
              <div className="mt-4 flex flex-wrap gap-2">
                <Button type="button" variant="secondary" disabled={reviewMutation.isPending} onClick={() => void submitReview("edit")}>
                  Save edits
                </Button>
                <Button type="button" disabled={reviewMutation.isPending} onClick={() => void submitReview("approve")}>
                  Approve
                </Button>
                <Button type="button" variant="ghost" disabled={reviewMutation.isPending} onClick={() => void submitReview("reject")}>
                  Reject
                </Button>
              </div>

              <div className="mt-5 border-t border-line pt-4">
                <p className="eyebrow">Audit trail</p>
                {(auditQuery.data?.items.length ?? 0) === 0 ? (
                  <p className="mt-2 text-sm text-slate">No UUID-linked audit events found for this document.</p>
                ) : (
                  <div className="mt-3 space-y-2">
                    {(auditQuery.data?.items ?? []).slice(0, 5).map((event) => (
                      <div key={event.id} className="rounded-xl bg-mist px-3 py-2">
                        <p className="text-sm font-semibold text-ink">{event.summary}</p>
                        <p className="mt-1 text-xs text-slate">{new Date(event.occurred_at).toLocaleString()}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </section>
      </div>
    </Card>
  );
}

import { ChangeEvent, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "@/api/errors";
import { AsyncContent } from "@/components/ui/AsyncContent";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { CaseStatusBadge } from "@/features/cases/components/CaseStatusBadge";
import {
  useCasesQuery,
  useCaseWorkspaceQuery,
  useCreateCaseMutation,
  useDeleteCaseMutation,
} from "@/features/cases/hooks";
import { DocumentManagementPanel } from "@/features/documents/components/DocumentManagementPanel";

export function DocumentIntakePage() {
  const casesQuery = useCasesQuery({ limit: 8, offset: 0 });
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedCaseId, setSelectedCaseId] = useState<string | undefined>(undefined);
  const [selectedLocalFile, setSelectedLocalFile] = useState<File | null>(null);
  const caseWorkspaceQuery = useCaseWorkspaceQuery(selectedCaseId);
  const deleteCaseMutation = useDeleteCaseMutation();
  const createCaseMutation = useCreateCaseMutation();
  const [createdCaseId, setCreatedCaseId] = useState<string | null>(null);
  const [createdCaseReference, setCreatedCaseReference] = useState<string | null>(null);
  const recentCases = casesQuery.data?.items ?? [];

  useEffect(() => {
    if (selectedCaseId && recentCases.length > 0 && !recentCases.some((item) => item.id === selectedCaseId)) {
      setSelectedCaseId(undefined);
    }
  }, [recentCases, selectedCaseId]);

  function selectCase(caseId: string) {
    setSelectedCaseId(caseId);
  }

  async function handleDeleteCase(caseId: string, caseReference: string) {
    const confirmed = window.confirm(
      `Delete case ${caseReference}? This removes all associated documents, extractions, and audit events.`,
    );
    if (!confirmed) {
      return;
    }

    try {
      await deleteCaseMutation.mutateAsync(caseId);
      if (selectedCaseId === caseId) {
        setSelectedCaseId(undefined);
      }
    } catch {
      window.alert("Case could not be deleted. Please try again.");
    }
  }

  async function handleFileInputChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setSelectedLocalFile(file);
    createCaseMutation.reset();
    setCreatedCaseId(null);
    setCreatedCaseReference(null);
    if (!file) return;

    try {
      const created = await createCaseMutation.mutateAsync({
        case_reference: `CASE-${Date.now()}`,
        case_type: "identity_document",
        source_channel: "manual_upload",
        current_queue: "document_ops",
        case_metadata: {
          source_filename: file.name,
          source_mime_type: file.type || "application/octet-stream",
          source_size_bytes: String(file.size),
        },
      });
      setCreatedCaseId(created.id);
      setCreatedCaseReference(created.case_reference);
    } catch {
      // error surfaces via mutation state below
    }
  }

  const createError = createCaseMutation.error;
  const createErrorMessage =
    createError instanceof ApiError
      ? createError.message
      : createError instanceof Error
        ? createError.message
        : null;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Documents"
        title="Document intake"
        description="Load a document to open a new case. Extraction runs as the next step after the case is created."
      />

      <Card
        title="Select case"
        description="Load a file to create a new case, or pick an existing case from the list below."
      >
        <div className="space-y-5">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.txt,.csv,.doc,.docx,.xls,.xlsx,application/pdf,image/*,text/plain,text/csv,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            onChange={(event) => void handleFileInputChange(event)}
            className="sr-only"
          />
          <div className="flex flex-col gap-3 md:flex-row">
            <Button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={createCaseMutation.isPending}
            >
              {createCaseMutation.isPending ? "Creating case..." : "Load documents"}
            </Button>
          </div>

          {selectedLocalFile ? (
            <div className="space-y-3 rounded-xl bg-mist px-3 py-3 text-sm text-slate">
              <p>
                Loaded file: <span className="font-semibold text-ink">{selectedLocalFile.name}</span>
              </p>

              {createErrorMessage ? (
                <p className="rounded-lg bg-dangerSoft px-3 py-2 text-xs text-danger">
                  Case could not be created: {createErrorMessage}
                </p>
              ) : null}

              {createdCaseId ? (
                <div className="rounded-lg bg-accentSoft px-3 py-2 text-xs text-ink">
                  <p className="font-semibold text-accent">Case created</p>
                  <p className="mt-1">
                    Reference: <span className="font-semibold">{createdCaseReference}</span>
                  </p>
                  <p className="mt-1 font-mono">UUID: {createdCaseId}</p>
                  <div className="mt-2 flex gap-3">
                    <button
                      type="button"
                      onClick={() => selectCase(createdCaseId)}
                      className="font-semibold text-accent underline-offset-4 hover:underline"
                    >
                      Open in intake panel
                    </button>
                    <Link
                      to={`/cases/${createdCaseId}`}
                      className="font-semibold text-accent underline-offset-4 hover:underline"
                    >
                      View case detail & audit trail
                    </Link>
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}

          <AsyncContent
            isLoading={casesQuery.isLoading}
            isError={casesQuery.isError}
            errorMessage="Recent cases could not be loaded."
            isEmpty={recentCases.length === 0}
            emptyTitle="No cases available"
            emptyMessage="Load a document above to create your first case."
            onRetry={() => void casesQuery.refetch()}
          >
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {recentCases.map((item) => (
                <div
                  key={item.id}
                  className={`flex flex-col gap-3 rounded-2xl border bg-white p-4 transition hover:border-accent hover:bg-accentSoft/50 ${
                    selectedCaseId === item.id ? "border-accent ring-2 ring-accentSoft" : "border-line"
                  }`}
                >
                  <button type="button" onClick={() => selectCase(item.id)} className="text-left">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate font-semibold text-ink">{item.case_reference}</p>
                        <p className="mt-1 truncate font-mono text-xs text-slate">{item.id}</p>
                      </div>
                      <CaseStatusBadge status={item.status} />
                    </div>
                    <div className="mt-3 text-sm font-semibold text-accent">
                      {selectedCaseId === item.id ? "Selected" : "Select case"}
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleDeleteCase(item.id, item.case_reference)}
                    disabled={deleteCaseMutation.isPending}
                    className="self-start rounded-lg border border-line px-3 py-1 text-xs font-semibold text-danger transition hover:bg-dangerSoft disabled:opacity-60"
                  >
                    {deleteCaseMutation.isPending && deleteCaseMutation.variables === item.id ? "Deleting..." : "Delete"}
                  </button>
                </div>
              ))}
            </div>
          </AsyncContent>

          <Link to="/cases" className="inline-flex text-sm font-semibold text-accent underline-offset-4 hover:underline">
            Create or view cases
          </Link>
        </div>
      </Card>

      {!selectedCaseId ? (
        <EmptyState title="No case selected" message="Select a case above to show document upload and document list controls." />
      ) : (
        <AsyncContent
          isLoading={caseWorkspaceQuery.isLoading}
          isError={caseWorkspaceQuery.isError}
          errorMessage="Case documents could not be loaded."
          isEmpty={!caseWorkspaceQuery.data}
          emptyTitle="Case not found"
          emptyMessage="The selected case was not returned by the backend."
          onRetry={() => void caseWorkspaceQuery.refetch()}
        >
          {caseWorkspaceQuery.data ? (
            <DocumentManagementPanel
              caseId={caseWorkspaceQuery.data.caseDetail.id}
              documents={caseWorkspaceQuery.data.caseDetail.documents}
              initialSelectedFile={selectedLocalFile}
              onInitialSelectedFileConsumed={() => setSelectedLocalFile(null)}
            />
          ) : null}
        </AsyncContent>
      )}
    </div>
  );
}

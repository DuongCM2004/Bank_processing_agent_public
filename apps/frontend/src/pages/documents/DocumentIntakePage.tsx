import { ChangeEvent, FormEvent, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { AsyncContent } from "@/components/ui/AsyncContent";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { CaseStatusBadge } from "@/features/cases/components/CaseStatusBadge";
import { useCasesQuery, useCaseWorkspaceQuery, useDeleteCaseMutation } from "@/features/cases/hooks";
import { DocumentManagementPanel } from "@/features/documents/components/DocumentManagementPanel";

export function DocumentIntakePage() {
  const casesQuery = useCasesQuery({ limit: 8, offset: 0 });
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [caseIdInput, setCaseIdInput] = useState("");
  const [selectedCaseId, setSelectedCaseId] = useState<string | undefined>(undefined);
  const [selectedLocalFile, setSelectedLocalFile] = useState<File | null>(null);
  const caseWorkspaceQuery = useCaseWorkspaceQuery(selectedCaseId);
  const deleteCaseMutation = useDeleteCaseMutation();
  const recentCases = casesQuery.data?.items ?? [];

  useEffect(() => {
    if (selectedCaseId && recentCases.length > 0 && !recentCases.some((item) => item.id === selectedCaseId)) {
      setSelectedCaseId(undefined);
      setCaseIdInput("");
    }
  }, [recentCases, selectedCaseId]);

  function selectCase(caseId: string) {
    setSelectedCaseId(caseId);
    setCaseIdInput(caseId);
  }

  async function handleDeleteCase(caseId: string, caseReference: string) {
    const confirmed = window.confirm(`Delete case ${caseReference}? This removes all associated documents, extractions, and audit events.`);
    if (!confirmed) {
      return;
    }

    try {
      await deleteCaseMutation.mutateAsync(caseId);
      if (selectedCaseId === caseId) {
        setSelectedCaseId(undefined);
        setCaseIdInput("");
      }
    } catch {
      window.alert("Case could not be deleted. Please try again.");
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSelectedCaseId(caseIdInput.trim() || undefined);
  }

  function handleFileInputChange(event: ChangeEvent<HTMLInputElement>) {
    setSelectedLocalFile(event.target.files?.[0] ?? null);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Documents"
        title="Document intake"
        description="Upload documents and review stored document records for a selected case."
      />

      <Card
        title="Select case"
        description="Documents are attached to a case. Choose an existing case first, then upload and extract in the intake panel."
      >
        <div className="space-y-5">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.txt,.csv,.doc,.docx,.xls,.xlsx,application/pdf,image/*,text/plain,text/csv,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            onChange={handleFileInputChange}
            className="sr-only"
          />
          <form onSubmit={handleSubmit} className="flex flex-col gap-3 md:flex-row">
            <input
              value={caseIdInput}
              onChange={(event) => setCaseIdInput(event.target.value)}
              placeholder="Enter case UUID"
              className="w-full rounded-xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none ring-accent transition focus:ring-2"
            />
            <Button type="submit">Load documents</Button>
            <Button type="button" variant="secondary" onClick={() => fileInputRef.current?.click()}>
              Stage local file
            </Button>
          </form>
          {selectedLocalFile ? (
            <p className="rounded-xl bg-mist px-3 py-2 text-sm text-slate">
              Staged local file: <span className="font-semibold text-ink">{selectedLocalFile.name}</span>
              {selectedCaseId ? " It is ready in the upload form below." : " Select a case to show the upload form."}
            </p>
          ) : null}

          <AsyncContent
            isLoading={casesQuery.isLoading}
            isError={casesQuery.isError}
            errorMessage="Recent cases could not be loaded."
            isEmpty={recentCases.length === 0}
            emptyTitle="No cases available"
            emptyMessage="Create a case first, then return here to upload documents."
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

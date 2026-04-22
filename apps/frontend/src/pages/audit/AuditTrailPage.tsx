import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/Button";
import { AsyncContent } from "@/components/ui/AsyncContent";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { AuditHistoryPanel } from "@/features/audit/components/AuditHistoryPanel";
import { useCaseAuditEventsQuery } from "@/features/audit/hooks";

export function AuditTrailPage() {
  const [caseIdInput, setCaseIdInput] = useState("");
  const [selectedCaseId, setSelectedCaseId] = useState<string | undefined>(undefined);
  const auditQuery = useCaseAuditEventsQuery({ caseId: selectedCaseId });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSelectedCaseId(caseIdInput.trim() || undefined);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Audit"
        title="Audit trail lookup"
        description="Structured event history intended for operational investigation and later compliance review."
      />

      <Card title="Find case audit events" description="Enter a case identifier to retrieve the event timeline from the backend.">
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 md:flex-row">
          <input
            value={caseIdInput}
            onChange={(event) => setCaseIdInput(event.target.value)}
            placeholder="Enter case UUID"
            className="w-full rounded-xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none ring-accent transition focus:ring-2"
          />
          <Button type="submit">Load audit trail</Button>
        </form>
      </Card>

      {!selectedCaseId ? (
        <EmptyState
          title="No case selected"
          message="Enter a case UUID to load structured audit events for a specific workflow history."
        />
      ) : (
        <AsyncContent
          isLoading={auditQuery.isLoading}
          isError={auditQuery.isError}
          errorMessage="Audit events could not be loaded."
          isEmpty={(auditQuery.data?.items.length ?? 0) === 0}
          emptyTitle="No audit events found"
          emptyMessage="The selected case did not return any audit events."
          onRetry={() => void auditQuery.refetch()}
        >
          <AuditHistoryPanel
            events={auditQuery.data?.items ?? []}
            totalEvents={auditQuery.data?.total}
            title="Audit events"
            description="Structured compliance-grade activity trail for this case."
          />
        </AsyncContent>
      )}
    </div>
  );
}

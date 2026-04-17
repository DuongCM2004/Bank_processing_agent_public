import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useCreateCaseMutation } from "@/features/cases/hooks";

function parseMetadata(value: string): Record<string, unknown> {
  if (value.trim().length === 0) {
    return {};
  }

  const parsed = JSON.parse(value) as unknown;
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error("Metadata must be a JSON object.");
  }

  return parsed as Record<string, unknown>;
}

export function CaseCreatePanel() {
  const createCaseMutation = useCreateCaseMutation();
  const [caseReference, setCaseReference] = useState("");
  const [caseType, setCaseType] = useState("loan_application");
  const [customerReference, setCustomerReference] = useState("");
  const [sourceChannel, setSourceChannel] = useState("manual_upload");
  const [currentQueue, setCurrentQueue] = useState("document_ops");
  const [actorId, setActorId] = useState("");
  const [metadataInput, setMetadataInput] = useState("{}");
  const [createdCaseId, setCreatedCaseId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFeedback(null);
    setCreatedCaseId(null);

    try {
      const created = await createCaseMutation.mutateAsync({
        case_reference: caseReference.trim(),
        case_type: caseType.trim(),
        customer_reference: customerReference.trim() || null,
        source_channel: sourceChannel.trim() || "manual_upload",
        current_queue: currentQueue.trim() || "document_ops",
        actor_id: actorId.trim() || null,
        case_metadata: parseMetadata(metadataInput),
      });
      setCaseReference("");
      setCustomerReference("");
      setCreatedCaseId(created.id);
      setFeedback("Case created.");
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "Case could not be created.");
    }
  }

  return (
    <Card title="Create case" description="Open a new document-processing case in the backend case queue.">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <label className="space-y-2 text-sm text-slate">
            <span className="font-medium text-ink">Case reference</span>
            <input
              value={caseReference}
              onChange={(event) => setCaseReference(event.target.value)}
              required
              maxLength={64}
              placeholder="CASE-2026-0001"
              className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-accent"
            />
          </label>
          <label className="space-y-2 text-sm text-slate">
            <span className="font-medium text-ink">Case type</span>
            <input
              value={caseType}
              onChange={(event) => setCaseType(event.target.value)}
              required
              maxLength={80}
              className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-accent"
            />
          </label>
          <label className="space-y-2 text-sm text-slate">
            <span className="font-medium text-ink">Customer reference</span>
            <input
              value={customerReference}
              onChange={(event) => setCustomerReference(event.target.value)}
              maxLength={120}
              placeholder="Optional"
              className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-accent"
            />
          </label>
          <label className="space-y-2 text-sm text-slate">
            <span className="font-medium text-ink">Source channel</span>
            <input
              value={sourceChannel}
              onChange={(event) => setSourceChannel(event.target.value)}
              maxLength={80}
              className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-accent"
            />
          </label>
          <label className="space-y-2 text-sm text-slate">
            <span className="font-medium text-ink">Current queue</span>
            <input
              value={currentQueue}
              onChange={(event) => setCurrentQueue(event.target.value)}
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
        </div>

        <label className="block space-y-2 text-sm text-slate">
          <span className="font-medium text-ink">Case metadata JSON</span>
          <textarea
            value={metadataInput}
            onChange={(event) => setMetadataInput(event.target.value)}
            rows={3}
            className="w-full rounded-2xl border border-line bg-white px-3 py-3 font-mono text-xs text-ink outline-none transition focus:border-accent"
          />
        </label>

        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" disabled={createCaseMutation.isPending}>
            Create case
          </Button>
          {feedback ? <span className="text-sm text-slate">{feedback}</span> : null}
          {createdCaseId ? (
            <Link to={`/cases/${createdCaseId}`} className="text-sm font-semibold text-accent underline-offset-4 hover:underline">
              Open created case
            </Link>
          ) : null}
        </div>
      </form>
    </Card>
  );
}

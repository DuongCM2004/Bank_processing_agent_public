import { FormEvent, useEffect, useMemo, useState } from "react";

import type { CaseDetail, CaseStatus, DecisionOutcome } from "@/api/contracts";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import {
  useCreateDecisionMutation,
  useQueueCaseProcessingMutation,
  useTransitionCaseStatusMutation,
} from "@/features/cases/hooks";

const nextStatusByStatus: Record<CaseStatus, CaseStatus[]> = {
  created: ["documents_uploaded"],
  documents_uploaded: ["queued_for_processing", "failed"],
  queued_for_processing: ["processing", "failed"],
  processing: ["extraction_completed", "failed"],
  extraction_completed: ["validation_completed", "failed"],
  validation_completed: ["manual_review_required", "decision_ready", "failed"],
  manual_review_required: ["decision_ready", "queued_for_processing", "failed"],
  decision_ready: ["approved", "rejected", "manual_review_required"],
  approved: [],
  rejected: [],
  failed: ["queued_for_processing"],
};

const decisionOutcomes: DecisionOutcome[] = ["approved", "rejected", "review_required", "escalated"];

export function CaseOperationsPanel({ caseDetail }: { caseDetail: CaseDetail }) {
  const transitionMutation = useTransitionCaseStatusMutation(caseDetail.id);
  const queueMutation = useQueueCaseProcessingMutation(caseDetail.id);
  const decisionMutation = useCreateDecisionMutation(caseDetail.id);
  const allowedStatuses = useMemo(() => nextStatusByStatus[caseDetail.status], [caseDetail.status]);

  const [actorId, setActorId] = useState("");
  const [targetStatus, setTargetStatus] = useState<CaseStatus>(allowedStatuses[0] ?? caseDetail.status);
  const [transitionComment, setTransitionComment] = useState("");
  const [decisionOutcome, setDecisionOutcome] = useState<DecisionOutcome>("approved");
  const [decisionRationale, setDecisionRationale] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);

  useEffect(() => {
    setTargetStatus(allowedStatuses[0] ?? caseDetail.status);
  }, [allowedStatuses, caseDetail.status]);

  async function handleTransition(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFeedback(null);

    try {
      await transitionMutation.mutateAsync({
        to_status: targetStatus,
        actor_type: "user",
        actor_id: actorId.trim() || null,
        reason_code: targetStatus,
        comment: transitionComment.trim() || null,
      });
      setTransitionComment("");
      setFeedback("Case status updated.");
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "Case status could not be updated.");
    }
  }

  async function handleQueueProcessing() {
    setFeedback(null);

    try {
      await queueMutation.mutateAsync({
        actor_id: actorId.trim() || null,
        reason_code: "queued_for_processing",
      });
      setFeedback("Case queued for processing.");
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "Case could not be queued.");
    }
  }

  async function handleDecision(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFeedback(null);

    try {
      await decisionMutation.mutateAsync({
        outcome: decisionOutcome,
        rationale: decisionRationale.trim(),
        actor_id: actorId.trim() || "system",
        decision_metadata: { source: "ops_web" },
        evidence_refs: [],
      });
      setDecisionRationale("");
      setFeedback("Decision recorded.");
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "Decision could not be recorded.");
    }
  }

  return (
    <Card
      title="Case actions"
      description="Backend-backed operations for intake, workflow movement, processing dispatch, and reviewer decisions."
    >
      <div className="space-y-5">
        <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px]">
          <label className="space-y-2 text-sm text-slate">
            <span className="font-medium text-ink">Actor ID</span>
            <input
              value={actorId}
              onChange={(event) => setActorId(event.target.value)}
              maxLength={128}
              placeholder="user-123"
              className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-accent"
            />
          </label>
          <div className="rounded-2xl border border-line p-4">
            <p className="eyebrow">Current backend status</p>
            <div className="mt-2">
              <StatusBadge tone="active">{caseDetail.status}</StatusBadge>
            </div>
          </div>
        </div>

        {feedback ? <div className="rounded-2xl border border-line bg-mist px-4 py-3 text-sm text-slate">{feedback}</div> : null}

        <div className="grid gap-5 xl:grid-cols-3">
          <form onSubmit={handleTransition} className="rounded-2xl border border-line p-4">
            <p className="eyebrow">Status transition</p>
            <div className="mt-4 grid gap-3">
              <select
                value={targetStatus}
                onChange={(event) => setTargetStatus(event.target.value as CaseStatus)}
                disabled={allowedStatuses.length === 0}
                className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-accent"
              >
                {allowedStatuses.length === 0 ? <option value={caseDetail.status}>No next status</option> : null}
                {allowedStatuses.map((status) => (
                  <option key={status} value={status}>
                    {status.split("_").join(" ")}
                  </option>
                ))}
              </select>
              <input
                value={transitionComment}
                onChange={(event) => setTransitionComment(event.target.value)}
                maxLength={500}
                placeholder="Optional transition comment"
                className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-accent"
              />
              <Button type="submit" disabled={allowedStatuses.length === 0 || transitionMutation.isPending}>
                Update status
              </Button>
            </div>
          </form>

          <div className="rounded-2xl border border-line p-4">
            <p className="eyebrow">Processing dispatch</p>
            <p className="mt-2 text-sm text-slate">Queue the case for backend processing after documents are uploaded.</p>
            <div className="mt-4">
              <Button type="button" onClick={() => void handleQueueProcessing()} disabled={queueMutation.isPending}>
                Queue processing
              </Button>
            </div>
          </div>

          <form onSubmit={handleDecision} className="rounded-2xl border border-line p-4">
            <p className="eyebrow">Decision</p>
            <div className="mt-4 grid gap-3">
              <select
                value={decisionOutcome}
                onChange={(event) => setDecisionOutcome(event.target.value as DecisionOutcome)}
                className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-accent"
              >
                {decisionOutcomes.map((outcome) => (
                  <option key={outcome} value={outcome}>
                    {outcome.split("_").join(" ")}
                  </option>
                ))}
              </select>
              <textarea
                value={decisionRationale}
                onChange={(event) => setDecisionRationale(event.target.value)}
                required
                rows={3}
                placeholder="Decision rationale"
                className="w-full rounded-2xl border border-line bg-white px-3 py-3 text-sm text-ink outline-none transition focus:border-accent"
              />
              <Button type="submit" disabled={decisionMutation.isPending}>
                Record decision
              </Button>
            </div>
          </form>
        </div>
      </div>
    </Card>
  );
}

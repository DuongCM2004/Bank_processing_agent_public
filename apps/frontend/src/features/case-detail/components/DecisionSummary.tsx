import { Panel } from "@/components/ui/Panel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { Decision } from "@/types/api";
import { formatDateTime, formatPercent } from "@/utils/format";

interface DecisionSummaryProps {
  decisions: Decision[];
}

export function DecisionSummary({ decisions }: DecisionSummaryProps) {
  const latestDecision = decisions[0];

  return (
    <Panel title="Decision summary" description="Decision output is read-only in this MVP and remains auditable through backend events.">
      {!latestDecision ? (
        <p className="text-sm text-muted">No decision has been recorded for this case.</p>
      ) : (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge
              label={latestDecision.outcome}
              tone={latestDecision.outcome === "approved" ? "success" : latestDecision.outcome === "rejected" ? "danger" : "warning"}
            />
            <span className="text-sm text-muted">{latestDecision.decision_type}</span>
          </div>
          <p className="text-sm leading-6 text-ink">{latestDecision.rationale ?? "No rationale provided."}</p>
          <dl className="grid gap-2 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-muted">Reason</dt>
              <dd className="font-semibold text-ink">{latestDecision.reason_code}</dd>
            </div>
            <div>
              <dt className="text-muted">Confidence</dt>
              <dd className="font-semibold text-ink">{formatPercent(latestDecision.confidence_score)}</dd>
            </div>
            <div>
              <dt className="text-muted">Recorded</dt>
              <dd className="font-semibold text-ink">{formatDateTime(latestDecision.created_at)}</dd>
            </div>
          </dl>
        </div>
      )}
    </Panel>
  );
}

import type { CaseStatus, ManualReviewAction } from "@/api/contracts";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";

interface ManualReviewStatusCardProps {
  caseStatus: CaseStatus;
  latestAction: ManualReviewAction | null;
  actionCount: number;
}

function isManualReviewActive(status: CaseStatus) {
  return status === "manual_review_required";
}

export function ManualReviewStatusCard({ caseStatus, latestAction, actionCount }: ManualReviewStatusCardProps) {
  return (
    <Card title="Manual review" description="Current reviewer intervention state and latest recorded reviewer action.">
      <div className="space-y-4">
        <div className="rounded-2xl border border-line p-4">
          <p className="eyebrow">Review state</p>
          <div className="mt-3">
            <StatusBadge tone={isManualReviewActive(caseStatus) ? "warning" : "neutral"}>
              {isManualReviewActive(caseStatus) ? "active" : "not active"}
            </StatusBadge>
          </div>
          <p className="mt-2 text-sm text-slate">{actionCount} manual review actions recorded for this case</p>
        </div>

        <div className="rounded-2xl border border-line p-4">
          <p className="eyebrow">Latest action</p>
          {latestAction ? (
            <>
              <p className="mt-2 text-base font-semibold text-ink">{latestAction.action_type.split("_").join(" ")}</p>
              <p className="mt-1 text-sm text-slate">{latestAction.comment ?? "No reviewer note recorded."}</p>
              <p className="mt-2 text-xs text-slate">Recorded {new Date(latestAction.created_at).toLocaleString()}</p>
            </>
          ) : (
            <p className="mt-2 text-sm text-slate">No manual review activity recorded yet.</p>
          )}
        </div>
      </div>
    </Card>
  );
}

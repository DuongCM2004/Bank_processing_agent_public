import type { Decision } from "@/api/contracts";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";

function outcomeTone(outcome: Decision["outcome"]) {
  if (outcome === "approved") {
    return "success";
  }
  if (outcome === "rejected") {
    return "danger";
  }
  return "warning";
}

export function DecisionSummaryCard({ decisions }: { decisions: Decision[] }) {
  return (
    <Card title="Decision summary" description="Latest decision records and linked findings that influenced the case outcome.">
      <div className="space-y-3">
        {decisions.length === 0 ? (
          <p className="text-sm text-slate">No decisions recorded yet.</p>
        ) : (
          decisions.map((decision) => (
            <div key={decision.id} className="rounded-2xl border border-line p-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <p className="font-semibold text-ink">{decision.outcome.split("_").join(" ")}</p>
                  <p className="mt-1 text-sm text-slate">{decision.reason_code}</p>
                  <p className="mt-2 text-xs text-slate">
                    {decision.linked_findings.length} linked findings · {decision.evidence_refs.length} evidence refs
                  </p>
                </div>
                <StatusBadge tone={outcomeTone(decision.outcome)}>{decision.outcome}</StatusBadge>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}

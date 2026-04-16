import { Panel } from "@/components/ui/Panel";
import { formatPercent } from "@/utils/format";

interface ExtractionSummaryProps {
  totalResults: number;
  completedResults: number;
  averageConfidence: number | null;
  schemas: string[];
}

export function ExtractionSummary({ totalResults, completedResults, averageConfidence, schemas }: ExtractionSummaryProps) {
  return (
    <Panel title="Extraction summary" description="Processing completeness and confidence overview before field-by-field review.">
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-md border border-line bg-surface p-3">
          <p className="text-xs font-bold uppercase tracking-wider text-muted">Completed</p>
          <p className="mt-1 text-xl font-semibold text-ink">
            {completedResults}/{totalResults}
          </p>
        </div>
        <div className="rounded-md border border-line bg-surface p-3">
          <p className="text-xs font-bold uppercase tracking-wider text-muted">Avg confidence</p>
          <p className="mt-1 text-xl font-semibold text-ink">{formatPercent(averageConfidence)}</p>
        </div>
        <div className="rounded-md border border-line bg-surface p-3">
          <p className="text-xs font-bold uppercase tracking-wider text-muted">Schemas</p>
          <p className="mt-1 text-sm font-semibold text-ink">{schemas.length > 0 ? schemas.join(", ") : "None"}</p>
        </div>
      </div>
    </Panel>
  );
}

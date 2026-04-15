import type { ExtractionResult } from "@/api/contracts";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";

interface ExtractionSummaryCardProps {
  totalResults: number;
  completedResults: number;
  averageConfidence: number | null;
  schemas: string[];
  results: ExtractionResult[];
}

function confidenceLabel(value: number | null) {
  if (value === null) {
    return "Not scored";
  }

  return `${Math.round(value * 100)}%`;
}

export function ExtractionSummaryCard({
  totalResults,
  completedResults,
  averageConfidence,
  schemas,
  results,
}: ExtractionSummaryCardProps) {
  return (
    <Card
      title="Extraction summary"
      description="Structured extraction outputs and confidence indicators. The section contract is designed for later evidence highlighting."
    >
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-line p-4">
          <p className="eyebrow">Results</p>
          <p className="mt-3 text-3xl font-semibold text-ink">{totalResults}</p>
          <p className="mt-1 text-sm text-slate">{completedResults} completed</p>
        </div>
        <div className="rounded-2xl border border-line p-4">
          <p className="eyebrow">Average confidence</p>
          <p className="mt-3 text-3xl font-semibold text-ink">{confidenceLabel(averageConfidence)}</p>
          <p className="mt-1 text-sm text-slate">Computed from extracted outputs</p>
        </div>
        <div className="rounded-2xl border border-line p-4">
          <p className="eyebrow">Schemas</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {schemas.length === 0 ? <span className="text-sm text-slate">No schemas detected</span> : null}
            {schemas.map((schema) => (
              <StatusBadge key={schema} tone="neutral">
                {schema}
              </StatusBadge>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {results.length === 0 ? (
          <p className="text-sm text-slate">No extraction outputs recorded.</p>
        ) : (
          results.map((result) => (
            <div key={result.id} className="rounded-2xl border border-line p-4" data-evidence-ready="true">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <p className="font-semibold text-ink">{result.schema_name}</p>
                  <p className="mt-1 text-sm text-slate">
                    Provider {result.provider_name} · {Object.keys(result.extracted_payload).length} extracted fields · {result.evidence_refs.length} evidence refs
                  </p>
                </div>
                <StatusBadge tone={result.status === "completed" ? "success" : "warning"}>{result.status}</StatusBadge>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}

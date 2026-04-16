import { Button } from "@/components/ui/Button";
import { Panel } from "@/components/ui/Panel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { ExtractionReviewField } from "@/types/viewModels";
import { formatPercent, humanize } from "@/utils/format";

interface ExtractionReviewPanelProps {
  totalFields: number;
  attentionCount: number;
  missingCount: number;
  ambiguousCount: number;
  fields: ExtractionReviewField[];
  onRequestCorrection: (field: ExtractionReviewField) => void;
}

export function ExtractionReviewPanel({
  totalFields,
  attentionCount,
  missingCount,
  ambiguousCount,
  fields,
  onRequestCorrection,
}: ExtractionReviewPanelProps) {
  return (
    <Panel
      title="Extraction review"
      description="Field-level raw values, normalized values, confidence, and correction entry points."
    >
      <div className="mb-4 grid gap-3 sm:grid-cols-4">
        {[
          ["Fields", totalFields],
          ["Attention", attentionCount],
          ["Missing", missingCount],
          ["Ambiguous", ambiguousCount],
        ].map(([label, value]) => (
          <div key={label} className="rounded-md border border-line bg-surface p-3">
            <p className="text-xs font-bold uppercase tracking-wider text-muted">{label}</p>
            <p className="mt-1 text-xl font-semibold text-ink">{value}</p>
          </div>
        ))}
      </div>

      {fields.length === 0 ? (
        <p className="text-sm text-muted">No extraction fields were returned by the backend.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-line">
          <table className="min-w-full divide-y divide-line text-sm">
            <thead className="bg-surface text-left text-xs font-bold uppercase tracking-wider text-muted">
              <tr>
                <th className="px-4 py-3">Field</th>
                <th className="px-4 py-3">Raw</th>
                <th className="px-4 py-3">Normalized</th>
                <th className="px-4 py-3">Confidence</th>
                <th className="px-4 py-3">Evidence</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line bg-panel">
              {fields.map((field) => (
                <tr key={field.id} className={field.needsAttention ? "bg-amberSoft/45" : undefined}>
                  <td className="px-4 py-3">
                    <p className="font-semibold text-ink">{humanize(field.fieldName)}</p>
                    <p className="mt-1 text-xs text-muted">{field.schemaName}</p>
                    <div className="mt-2 flex gap-1">
                      {field.isMissing ? <StatusBadge label="Missing" tone="danger" /> : null}
                      {field.isAmbiguous ? <StatusBadge label="Ambiguous" tone="warning" /> : null}
                    </div>
                  </td>
                  <td className="max-w-[220px] px-4 py-3 text-ink">{field.rawValue ?? "Missing"}</td>
                  <td className="max-w-[220px] px-4 py-3 text-ink">{field.normalizedValue ?? "Not normalized"}</td>
                  <td className="px-4 py-3 font-mono text-ink">{formatPercent(field.confidence)}</td>
                  <td className="max-w-[240px] px-4 py-3 text-muted">
                    {field.evidenceSnippet ?? "No evidence snippet"}
                    {field.evidencePageNumber ? <span className="block text-xs">Page {field.evidencePageNumber}</span> : null}
                  </td>
                  <td className="px-4 py-3">
                    <Button type="button" onClick={() => onRequestCorrection(field)}>
                      Correct
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}

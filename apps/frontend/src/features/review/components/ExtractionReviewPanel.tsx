import type { ExtractionReviewField } from "@/features/cases/workspace";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";

interface ExtractionReviewPanelProps {
  fields: ExtractionReviewField[];
  totalFields: number;
  attentionCount: number;
  missingCount: number;
  ambiguousCount: number;
  onRequestCorrection?: (field: ExtractionReviewField) => void;
}

function confidenceLabel(value: number | null) {
  if (value === null) {
    return "Unscored";
  }

  return `${Math.round(value * 100)}%`;
}

function confidenceTone(value: number | null) {
  if (value === null) {
    return "warning" as const;
  }

  if (value >= 0.9) {
    return "success" as const;
  }

  if (value >= 0.8) {
    return "active" as const;
  }

  return "warning" as const;
}

function prettifyFieldName(value: string) {
  return value.split("_").join(" ");
}

export function ExtractionReviewPanel({
  fields,
  totalFields,
  attentionCount,
  missingCount,
  ambiguousCount,
  onRequestCorrection,
}: ExtractionReviewPanelProps) {
  return (
    <Card
      title="Extraction review"
      description="Field-level extraction outputs with confidence and evidence cues so reviewers can confirm or correct data quickly."
    >
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-2xl border border-line p-4">
          <p className="eyebrow">Fields</p>
          <p className="mt-3 text-3xl font-semibold text-ink">{totalFields}</p>
          <p className="mt-1 text-sm text-slate">Flattened extracted values</p>
        </div>
        <div className="rounded-2xl border border-line p-4">
          <p className="eyebrow">Needs attention</p>
          <p className="mt-3 text-3xl font-semibold text-warning">{attentionCount}</p>
          <p className="mt-1 text-sm text-slate">Missing or uncertain fields</p>
        </div>
        <div className="rounded-2xl border border-line p-4">
          <p className="eyebrow">Missing</p>
          <p className="mt-3 text-3xl font-semibold text-danger">{missingCount}</p>
          <p className="mt-1 text-sm text-slate">No usable extracted value</p>
        </div>
        <div className="rounded-2xl border border-line p-4">
          <p className="eyebrow">Ambiguous</p>
          <p className="mt-3 text-3xl font-semibold text-accent">{ambiguousCount}</p>
          <p className="mt-1 text-sm text-slate">Low-confidence or flagged fields</p>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {fields.length === 0 ? (
          <p className="text-sm text-slate">No extracted fields are available for review yet.</p>
        ) : (
          fields.map((field) => (
            <div
              key={field.id}
              className="rounded-2xl border border-line bg-white p-4"
              data-evidence-ready="true"
              data-review-attention={field.needsAttention}
            >
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0 flex-1 space-y-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-sm font-semibold uppercase tracking-wide text-ink">{prettifyFieldName(field.fieldName)}</h3>
                    <StatusBadge tone="neutral">{field.schemaName}</StatusBadge>
                    <StatusBadge tone={confidenceTone(field.confidence)}>{confidenceLabel(field.confidence)}</StatusBadge>
                    {field.isMissing ? <StatusBadge tone="danger">missing</StatusBadge> : null}
                    {field.isAmbiguous ? <StatusBadge tone="warning">ambiguous</StatusBadge> : null}
                  </div>

                  <div className="grid gap-3 md:grid-cols-2">
                    <div className="rounded-xl bg-mist px-3 py-3">
                      <p className="eyebrow">Raw value</p>
                      <p className="mt-2 text-sm text-ink">{field.rawValue ?? "No extracted value"}</p>
                    </div>
                    <div className="rounded-xl bg-mist px-3 py-3">
                      <p className="eyebrow">Normalized value</p>
                      <p className="mt-2 text-sm text-ink">{field.normalizedValue ?? "No normalized value"}</p>
                    </div>
                  </div>

                  <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_180px]">
                    <div className="rounded-xl border border-dashed border-line px-3 py-3">
                      <p className="eyebrow">Evidence snippet</p>
                      <p className="mt-2 text-sm text-slate">{field.evidenceSnippet ?? "No evidence snippet attached"}</p>
                    </div>
                    <div className="rounded-xl border border-dashed border-line px-3 py-3">
                      <p className="eyebrow">Evidence page</p>
                      <p className="mt-2 text-sm text-slate">{field.evidencePageNumber ?? "Not mapped"}</p>
                    </div>
                  </div>
                </div>

                <div className="flex min-w-[148px] flex-col gap-2">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => onRequestCorrection?.(field)}
                    disabled={!onRequestCorrection}
                  >
                    Manual correction
                  </Button>
                  <p className="text-xs leading-5 text-slate">
                    {field.needsAttention
                      ? "Review is recommended before final decisioning."
                      : "Field looks stable but can still be corrected if needed."}
                  </p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}

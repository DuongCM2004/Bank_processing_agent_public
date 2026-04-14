import { EmptyState } from "@/components/empty-state";
import type { FieldResult } from "@/lib/types";

export function ExtractionReviewPanel({ fields }: { fields: FieldResult[] }) {
  if (fields.length === 0) {
    return (
      <EmptyState
        title="No extracted fields"
        detail="Extraction results have not been produced yet or the workflow is waiting on upstream processing."
      />
    );
  }

  return (
    <section className="panel">
      <h2>Extraction Review</h2>
      <p className="muted">Machine outputs remain visible so the reviewer can compare extracted values against evidence.</p>
      <div className="field-card">
        {fields.map((field) => (
          <div className="field-row" key={field.field_name}>
            <div className="field-label">{field.field_name}</div>
            <div className="field-value">
              <div className="muted">Extracted</div>
              <div>{field.value ?? "missing"}</div>
            </div>
            <div className="field-value">
              <div className="muted">Normalized / confidence</div>
              <div>{field.normalized_value ?? "missing"}</div>
              <div className="muted">Confidence: {field.confidence ?? "n/a"}</div>
              <div className="muted">Reason: {field.reason_code ?? "none"}</div>
              <div className="muted">Evidence links: {field.evidence_refs.length}</div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

import type { FieldResult } from "@/lib/types";

export function FieldComparisonPanel({ fields }: { fields: FieldResult[] }) {
  return (
    <div className="panel">
      <h2>Field Comparison</h2>
      <p className="muted">Machine result remains visible; reviewers compare normalized values against cited evidence.</p>
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
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

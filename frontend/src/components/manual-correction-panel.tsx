import type { CorrectionDraft, FieldResult } from "@/lib/types";

function buildDrafts(fields: FieldResult[]): CorrectionDraft[] {
  return fields.map((field) => ({
    field_name: field.field_name,
    current_value: field.value,
    corrected_value: field.normalized_value ?? field.value ?? "",
    reason_code: field.reason_code ?? "reviewer_confirmed",
    reviewer_comment: "",
  }));
}

export function ManualCorrectionPanel({ fields }: { fields: FieldResult[] }) {
  const drafts = buildDrafts(fields);

  return (
    <section className="panel">
      <h2>Manual Correction Flow</h2>
      <p className="muted">Starter scaffold for reviewer-confirmed corrections. Original machine outputs remain visible.</p>
      <div className="correction-list">
        {drafts.map((draft) => (
          <div key={draft.field_name} className="correction-card">
            <div>
              <strong>{draft.field_name}</strong>
              <div className="muted">Current: {draft.current_value ?? "missing"}</div>
            </div>
            <label className="form-field">
              <span className="muted">Corrected value</span>
              <input defaultValue={draft.corrected_value} />
            </label>
            <label className="form-field">
              <span className="muted">Reason code</span>
              <input defaultValue={draft.reason_code} />
            </label>
            <label className="form-field">
              <span className="muted">Reviewer comment</span>
              <textarea defaultValue={draft.reviewer_comment} rows={3} />
            </label>
          </div>
        ))}
      </div>
    </section>
  );
}

import { useEffect, useMemo, useState } from "react";

import { useCurrentUser } from "@/app/providers";
import { Button } from "@/components/ui/Button";
import { Panel } from "@/components/ui/Panel";
import { RoleGate } from "@/components/common/RoleGate";
import { addManualReviewNote, resubmitManualReviewCase, submitManualCorrections } from "@/services/api/manualReview";
import type { CaseStatus, ManualReviewAction } from "@/types/api";
import type { ExtractionReviewField } from "@/types/viewModels";
import { formatDateTime, humanize } from "@/utils/format";

interface ManualReviewPanelProps {
  caseId: string;
  caseStatus: CaseStatus;
  actions: ManualReviewAction[];
  fields: ExtractionReviewField[];
  selectedFieldId: string | null;
  onSelectedFieldChange: (fieldId: string | null) => void;
  onSubmitted: () => void;
}

export function ManualReviewPanel({
  caseId,
  caseStatus,
  actions,
  fields,
  selectedFieldId,
  onSelectedFieldChange,
  onSubmitted,
}: ManualReviewPanelProps) {
  const user = useCurrentUser();
  const [note, setNote] = useState("");
  const [correctedValue, setCorrectedValue] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const selectedField = useMemo(
    () => fields.find((field) => field.id === selectedFieldId) ?? fields.find((field) => field.needsAttention) ?? fields[0] ?? null,
    [fields, selectedFieldId],
  );

  useEffect(() => {
    if (selectedField && !selectedFieldId) {
      onSelectedFieldChange(selectedField.id);
    }
  }, [onSelectedFieldChange, selectedField, selectedFieldId]);

  async function submitNote() {
    if (!note.trim()) {
      setMessage("Reviewer note is required.");
      return;
    }

    setIsSubmitting(true);
    setMessage(null);
    try {
      await addManualReviewNote(caseId, {
        performed_by_user_id: user.id,
        comment: note.trim(),
      });
      setNote("");
      setMessage("Reviewer note recorded.");
      onSubmitted();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to record note.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function submitCorrection() {
    if (!selectedField || !correctedValue.trim()) {
      setMessage("Select a field and enter a corrected value.");
      return;
    }

    setIsSubmitting(true);
    setMessage(null);
    try {
      await submitManualCorrections(caseId, {
        performed_by_user_id: user.id,
        comment: note.trim() || undefined,
        corrections: [
          {
            extraction_result_id: selectedField.extractionResultId,
            field_name: selectedField.fieldName,
            before_value: selectedField.normalizedValue ?? selectedField.rawValue,
            after_value: correctedValue.trim(),
          },
        ],
      });
      setCorrectedValue("");
      setMessage("Manual correction submitted.");
      onSubmitted();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to submit correction.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function resubmit(target_status: "decision_ready" | "queued_for_processing") {
    setIsSubmitting(true);
    setMessage(null);
    try {
      await resubmitManualReviewCase(caseId, {
        performed_by_user_id: user.id,
        target_status,
        comment: note.trim() || undefined,
        reason_code: target_status === "decision_ready" ? "review_complete" : "needs_reprocessing",
      });
      setMessage(target_status === "decision_ready" ? "Case sent to decisioning." : "Case sent to reprocessing.");
      onSubmitted();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to resubmit case.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Panel title="Manual review" description="Reviewer notes, corrected value submission, and workflow handoff controls.">
      <RoleGate
        minRole="reviewer"
        fallback={<p className="text-sm text-muted">Current role can view review data but cannot submit manual actions.</p>}
      >
        <div className="space-y-4">
          <label className="block text-sm font-semibold text-ink">
            Correction field
            <select
              className="mt-2 w-full rounded-md border border-line bg-white px-3 py-2 text-sm"
              value={selectedField?.id ?? ""}
              onChange={(event) => onSelectedFieldChange(event.target.value)}
            >
              {fields.map((field) => (
                <option key={field.id} value={field.id}>
                  {humanize(field.fieldName)} ({field.schemaName})
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm font-semibold text-ink">
            Corrected value
            <input
              className="mt-2 w-full rounded-md border border-line bg-white px-3 py-2 text-sm"
              value={correctedValue}
              onChange={(event) => setCorrectedValue(event.target.value)}
              placeholder={selectedField?.normalizedValue ?? selectedField?.rawValue ?? "Enter corrected value"}
            />
          </label>
          <label className="block text-sm font-semibold text-ink">
            Reviewer note
            <textarea
              className="mt-2 min-h-24 w-full rounded-md border border-line bg-white px-3 py-2 text-sm"
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder="Record correction reason, hold rationale, or escalation context."
            />
          </label>
          {message ? <p className="rounded-md border border-line bg-surface p-3 text-sm text-ink">{message}</p> : null}
          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={submitNote} disabled={isSubmitting}>
              Add note
            </Button>
            <Button type="button" variant="primary" onClick={submitCorrection} disabled={isSubmitting || fields.length === 0}>
              Submit correction
            </Button>
            <Button type="button" onClick={() => resubmit("decision_ready")} disabled={isSubmitting || caseStatus === "decision_ready"}>
              Send to decisioning
            </Button>
            <Button type="button" variant="danger" onClick={() => resubmit("queued_for_processing")} disabled={isSubmitting}>
              Hold and reprocess
            </Button>
          </div>
        </div>
      </RoleGate>

      <div className="mt-6 border-t border-line pt-4">
        <p className="text-sm font-semibold text-ink">Recent manual actions</p>
        {actions.length === 0 ? (
          <p className="mt-2 text-sm text-muted">No manual review actions have been recorded.</p>
        ) : (
          <div className="mt-2 space-y-2">
            {actions.slice(0, 3).map((action) => (
              <article key={action.id} className="rounded-md border border-line bg-surface p-3">
                <p className="text-sm font-semibold text-ink">{humanize(action.action_type)}</p>
                <p className="mt-1 text-xs text-muted">
                  {action.comment ?? "No comment"} | {formatDateTime(action.created_at)}
                </p>
              </article>
            ))}
          </div>
        )}
      </div>
    </Panel>
  );
}

import { useEffect, useMemo, useState } from "react";

import type {
  CaseStatus,
  ManualCorrectionSubmissionRequest,
  ManualReviewAction,
  ManualReviewNoteRequest,
  ManualReviewResubmitRequest,
} from "@/api/contracts";
import type { ExtractionReviewField } from "@/features/cases/workspace";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";

interface ManualReviewFlowPanelProps {
  caseStatus: CaseStatus;
  fields: ExtractionReviewField[];
  actions: ManualReviewAction[];
  selectedFieldId?: string | null;
  onSelectedFieldChange?: (fieldId: string) => void;
  onAddNote: (request: ManualReviewNoteRequest) => Promise<unknown>;
  onSubmitCorrections: (request: ManualCorrectionSubmissionRequest) => Promise<unknown>;
  onResubmit: (request: ManualReviewResubmitRequest) => Promise<unknown>;
  isSubmittingNote?: boolean;
  isSubmittingCorrections?: boolean;
  isSubmittingWorkflow?: boolean;
}

interface StagedCorrection {
  fieldId: string;
  extractionResultId: string;
  fieldName: string;
  beforeValue: unknown | null;
  afterValue: unknown | null;
}

type FeedbackTone = "success" | "danger";

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "No value";
  }

  if (typeof value === "string") {
    return value;
  }

  return JSON.stringify(value);
}

function fieldLabel(field: ExtractionReviewField) {
  return `${field.fieldName.split("_").join(" ")} (${field.schemaName})`;
}

function activeTone(status: CaseStatus) {
  return status === "manual_review_required" ? "warning" : "neutral";
}

export function ManualReviewFlowPanel({
  caseStatus,
  fields,
  actions,
  selectedFieldId,
  onSelectedFieldChange,
  onAddNote,
  onSubmitCorrections,
  onResubmit,
  isSubmittingNote = false,
  isSubmittingCorrections = false,
  isSubmittingWorkflow = false,
}: ManualReviewFlowPanelProps) {
  const fieldOptions = useMemo(() => fields, [fields]);
  const [reviewerUserId, setReviewerUserId] = useState("");
  const [reviewerLabel, setReviewerLabel] = useState("");
  const [noteInput, setNoteInput] = useState("");
  const [correctionComment, setCorrectionComment] = useState("");
  const [workflowComment, setWorkflowComment] = useState("");
  const [resubmitTarget, setResubmitTarget] = useState<ManualReviewResubmitRequest["target_status"]>("decision_ready");
  const [activeFieldId, setActiveFieldId] = useState<string>(selectedFieldId ?? fieldOptions[0]?.id ?? "");
  const [correctedValueInput, setCorrectedValueInput] = useState("");
  const [stagedCorrections, setStagedCorrections] = useState<StagedCorrection[]>([]);
  const [feedback, setFeedback] = useState<{ tone: FeedbackTone; message: string } | null>(null);

  useEffect(() => {
    if (selectedFieldId) {
      setActiveFieldId(selectedFieldId);
      return;
    }

    if (!activeFieldId && fieldOptions.length > 0) {
      setActiveFieldId(fieldOptions[0].id);
    }
  }, [activeFieldId, fieldOptions, selectedFieldId]);

  const activeField = fieldOptions.find((field) => field.id === activeFieldId) ?? null;
  const reviewerReady = reviewerUserId.trim().length > 0;

  function updateFieldSelection(fieldId: string) {
    setActiveFieldId(fieldId);
    onSelectedFieldChange?.(fieldId);
    setCorrectedValueInput("");
  }

  function showFeedback(tone: FeedbackTone, message: string) {
    setFeedback({ tone, message });
  }

  async function handleAddNote(mode: "note" | "hold") {
    if (!reviewerReady || noteInput.trim().length === 0) {
      showFeedback("danger", "Reviewer user ID and note text are required.");
      return;
    }

    const comment = mode === "hold" ? `[Hold] ${noteInput.trim()}` : noteInput.trim();

    try {
      await onAddNote({
        performed_by_user_id: reviewerUserId.trim(),
        comment,
      });
      setNoteInput("");
      showFeedback("success", mode === "hold" ? "Review hold was recorded." : "Reviewer note was recorded.");
    } catch (error) {
      showFeedback("danger", error instanceof Error ? error.message : "The reviewer note could not be recorded.");
    }
  }

  function handleStageCorrection() {
    if (!reviewerReady || !activeField) {
      showFeedback("danger", "Select a field and enter the reviewer user ID before staging a correction.");
      return;
    }

    if (correctedValueInput.trim().length === 0) {
      showFeedback("danger", "Enter a corrected value before staging the correction.");
      return;
    }

    const nextCorrection: StagedCorrection = {
      fieldId: activeField.id,
      extractionResultId: activeField.extractionResultId,
      fieldName: activeField.fieldName,
      beforeValue: activeField.normalizedValue ?? activeField.rawValue,
      afterValue: correctedValueInput.trim(),
    };

    setStagedCorrections((current) => {
      const withoutExisting = current.filter((item) => item.fieldId !== nextCorrection.fieldId);
      return [...withoutExisting, nextCorrection];
    });
    setCorrectedValueInput("");
    showFeedback("success", "Correction staged. Submit corrections to persist reviewer edits.");
  }

  async function handleSubmitCorrections() {
    if (!reviewerReady || stagedCorrections.length === 0) {
      showFeedback("danger", "Reviewer user ID and at least one staged correction are required.");
      return;
    }

    try {
      await onSubmitCorrections({
        performed_by_user_id: reviewerUserId.trim(),
        comment: correctionComment.trim() || undefined,
        corrections: stagedCorrections.map((correction) => ({
          extraction_result_id: correction.extractionResultId,
          field_name: correction.fieldName,
          before_value: correction.beforeValue,
          after_value: correction.afterValue,
          evidence_refs: [],
        })),
      });
      setStagedCorrections([]);
      setCorrectionComment("");
      showFeedback("success", "Corrections were submitted for manual review.");
    } catch (error) {
      showFeedback("danger", error instanceof Error ? error.message : "Corrections could not be submitted.");
    }
  }

  async function handleResubmit() {
    if (!reviewerReady) {
      showFeedback("danger", "Reviewer user ID is required before resubmitting the case.");
      return;
    }

    try {
      await onResubmit({
        performed_by_user_id: reviewerUserId.trim(),
        target_status: resubmitTarget,
        comment: workflowComment.trim() || undefined,
      });
      setWorkflowComment("");
      showFeedback(
        "success",
        resubmitTarget === "decision_ready" ? "Case was resubmitted for decisioning." : "Case was resubmitted for reprocessing.",
      );
    } catch (error) {
      showFeedback("danger", error instanceof Error ? error.message : "Case resubmission failed.");
    }
  }

  return (
    <Card
      title="Manual review flow"
      description="Explicit reviewer actions for notes, corrections, and workflow resubmission. Reviewer attribution is captured here until authenticated identity is wired in."
    >
      <div className="space-y-5">
        <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px]">
          <div className="rounded-2xl border border-line p-4">
            <p className="eyebrow">Reviewer attribution</p>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <label className="space-y-2 text-sm text-slate">
                <span className="font-medium text-ink">Reviewer user ID</span>
                <input
                  value={reviewerUserId}
                  onChange={(event) => setReviewerUserId(event.target.value)}
                  placeholder="user-123"
                  className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-accent"
                />
              </label>
              <label className="space-y-2 text-sm text-slate">
                <span className="font-medium text-ink">Reviewer label</span>
                <input
                  value={reviewerLabel}
                  onChange={(event) => setReviewerLabel(event.target.value)}
                  placeholder="Optional display label"
                  className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-accent"
                />
              </label>
            </div>
          </div>

          <div className="rounded-2xl border border-line p-4">
            <p className="eyebrow">Review state</p>
            <div className="mt-3 flex items-center gap-2">
              <StatusBadge tone={activeTone(caseStatus)}>{caseStatus}</StatusBadge>
              {reviewerReady ? <StatusBadge tone="active">reviewer set</StatusBadge> : <StatusBadge tone="neutral">reviewer missing</StatusBadge>}
            </div>
            <p className="mt-3 text-sm text-slate">{reviewerLabel.trim() || reviewerUserId.trim() || "No reviewer attribution entered yet."}</p>
          </div>
        </div>

        {feedback ? (
          <div
            className={`rounded-2xl border px-4 py-3 text-sm ${
              feedback.tone === "success" ? "border-[#cfe9d9] bg-[#f4fbf6] text-[#137547]" : "border-dangerSoft bg-[#fff4f4] text-danger"
            }`}
          >
            {feedback.message}
          </div>
        ) : null}

        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
          <section className="space-y-5">
            <div className="rounded-2xl border border-line p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="eyebrow">Reviewer note</p>
                  <p className="mt-1 text-sm text-slate">Notes are explicit review actions. Hold keeps the case in manual review and records the note with a hold marker.</p>
                </div>
                <StatusBadge tone="neutral">{String(actions.length)}</StatusBadge>
              </div>
              <textarea
                value={noteInput}
                onChange={(event) => setNoteInput(event.target.value)}
                rows={4}
                placeholder="Explain the reviewer observation or reason for holding the case."
                className="mt-4 w-full rounded-2xl border border-line bg-white px-3 py-3 text-sm text-ink outline-none transition focus:border-accent"
              />
              <div className="mt-3 flex flex-wrap gap-3">
                <Button type="button" variant="secondary" onClick={() => void handleAddNote("note")} disabled={isSubmittingNote}>
                  Add reviewer note
                </Button>
                <Button type="button" onClick={() => void handleAddNote("hold")} disabled={isSubmittingNote}>
                  Hold review
                </Button>
              </div>
            </div>

            <div className="rounded-2xl border border-line p-4">
              <p className="eyebrow">Field correction</p>
              <p className="mt-1 text-sm text-slate">Choose a field, compare the extracted value to the corrected value, and stage the edit before submission.</p>

              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <label className="space-y-2 text-sm text-slate">
                  <span className="font-medium text-ink">Field</span>
                  <select
                    value={activeFieldId}
                    onChange={(event) => updateFieldSelection(event.target.value)}
                    className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-accent"
                  >
                    {fieldOptions.map((field) => (
                      <option key={field.id} value={field.id}>
                        {fieldLabel(field)}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="space-y-2 text-sm text-slate">
                  <span className="font-medium text-ink">Corrected value</span>
                  <input
                    value={correctedValueInput}
                    onChange={(event) => setCorrectedValueInput(event.target.value)}
                    placeholder="Enter corrected field value"
                    className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-accent"
                  />
                </label>
              </div>

              {activeField ? (
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <div className="rounded-2xl bg-mist px-4 py-4">
                    <p className="eyebrow">Previous extracted value</p>
                    <p className="mt-2 text-sm text-ink">{formatValue(activeField.normalizedValue ?? activeField.rawValue)}</p>
                  </div>
                  <div className="rounded-2xl bg-mist px-4 py-4">
                    <p className="eyebrow">Pending corrected value</p>
                    <p className="mt-2 text-sm text-ink">{correctedValueInput.trim() || "No corrected value entered yet."}</p>
                  </div>
                </div>
              ) : (
                <p className="mt-4 text-sm text-slate">No extracted fields are available for manual correction.</p>
              )}

              <label className="mt-4 block space-y-2 text-sm text-slate">
                <span className="font-medium text-ink">Correction note</span>
                <textarea
                  value={correctionComment}
                  onChange={(event) => setCorrectionComment(event.target.value)}
                  rows={3}
                  placeholder="Optional rationale for the submitted corrections."
                  className="w-full rounded-2xl border border-line bg-white px-3 py-3 text-sm text-ink outline-none transition focus:border-accent"
                />
              </label>

              <div className="mt-3 flex flex-wrap gap-3">
                <Button type="button" variant="secondary" onClick={handleStageCorrection}>
                  Stage correction
                </Button>
                <Button type="button" onClick={() => void handleSubmitCorrections()} disabled={isSubmittingCorrections}>
                  Submit corrections
                </Button>
              </div>
            </div>

            <div className="rounded-2xl border border-line p-4">
              <p className="eyebrow">Workflow action</p>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <label className="space-y-2 text-sm text-slate">
                  <span className="font-medium text-ink">Resubmit target</span>
                  <select
                    value={resubmitTarget}
                    onChange={(event) => setResubmitTarget(event.target.value as ManualReviewResubmitRequest["target_status"])}
                    className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-accent"
                  >
                    <option value="decision_ready">Continue to decision</option>
                    <option value="queued_for_processing">Request reprocessing</option>
                  </select>
                </label>
                <label className="space-y-2 text-sm text-slate">
                  <span className="font-medium text-ink">Workflow comment</span>
                  <input
                    value={workflowComment}
                    onChange={(event) => setWorkflowComment(event.target.value)}
                    placeholder="Optional resubmission note"
                    className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-accent"
                  />
                </label>
              </div>
              <div className="mt-3">
                <Button type="button" onClick={() => void handleResubmit()} disabled={isSubmittingWorkflow}>
                  Resubmit case
                </Button>
              </div>
            </div>
          </section>

          <aside className="space-y-5">
            <div className="rounded-2xl border border-line p-4">
              <p className="eyebrow">Staged corrections</p>
              {stagedCorrections.length === 0 ? (
                <p className="mt-3 text-sm text-slate">No field corrections staged yet.</p>
              ) : (
                <div className="mt-3 space-y-3">
                  {stagedCorrections.map((correction) => (
                    <div key={correction.fieldId} className="rounded-2xl bg-mist px-4 py-4">
                      <p className="text-sm font-semibold text-ink">{correction.fieldName.split("_").join(" ")}</p>
                      <div className="mt-3 grid gap-3 md:grid-cols-2">
                        <div>
                          <p className="eyebrow">Before</p>
                          <p className="mt-1 text-sm text-slate">{formatValue(correction.beforeValue)}</p>
                        </div>
                        <div>
                          <p className="eyebrow">After</p>
                          <p className="mt-1 text-sm text-ink">{formatValue(correction.afterValue)}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="rounded-2xl border border-line p-4">
              <p className="eyebrow">Previous review actions</p>
              {actions.length === 0 ? (
                <p className="mt-3 text-sm text-slate">No previous reviewer actions recorded.</p>
              ) : (
                <div className="mt-3 space-y-3">
                  {actions.slice(0, 5).map((action) => (
                    <div key={action.id} className="rounded-2xl border border-line bg-white px-4 py-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <StatusBadge tone="neutral">{action.action_type}</StatusBadge>
                        <span className="text-xs text-slate">{action.performed_by_user_id}</span>
                      </div>
                      <p className="mt-2 text-sm text-slate">{action.comment ?? "No reviewer comment recorded."}</p>
                      <p className="mt-2 text-xs text-slate">{new Date(action.created_at).toLocaleString()}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </aside>
        </div>
      </div>
    </Card>
  );
}

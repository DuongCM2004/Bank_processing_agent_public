import type { CaseStatus } from "@/api/contracts";
import { StatusBadge } from "@/components/ui/StatusBadge";

const tones: Record<CaseStatus, "neutral" | "active" | "warning" | "danger" | "success"> = {
  created: "neutral",
  documents_uploaded: "active",
  queued_for_processing: "active",
  processing: "active",
  extraction_completed: "active",
  validation_completed: "active",
  manual_review_required: "warning",
  decision_ready: "warning",
  approved: "success",
  rejected: "danger",
  failed: "danger",
};

export function CaseStatusBadge({ status }: { status: CaseStatus }) {
  return <StatusBadge tone={tones[status]}>{status}</StatusBadge>;
}

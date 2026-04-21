import type { DocumentStatus } from "@/api/contracts";
import type { StatusBadgeTone } from "@/components/ui/StatusBadge";

export const documentStatusTones: Record<DocumentStatus, StatusBadgeTone> = {
  uploaded: "active",
  stored: "active",
  queued: "warning",
  preprocessing: "warning",
  extracting: "warning",
  validating: "warning",
  retrying: "warning",
  extracted: "active",
  in_review: "warning",
  approved: "success",
  rejected: "danger",
  persisted: "success",
  ocr_pending: "warning",
  ocr_completed: "active",
  extraction_completed: "success",
  review_required: "warning",
  failed: "danger",
  archived: "neutral",
};

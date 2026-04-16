import type { CaseStatus, FindingSeverity, RiskLevel } from "@/types/api";

export function caseStatusTone(status: CaseStatus) {
  if (status === "manual_review_required" || status === "failed" || status === "rejected") {
    return "danger" as const;
  }

  if (status === "processing" || status === "queued_for_processing") {
    return "info" as const;
  }

  if (status === "validation_completed" || status === "decision_ready") {
    return "warning" as const;
  }

  if (status === "approved" || status === "extraction_completed") {
    return "success" as const;
  }

  return "neutral" as const;
}

export function severityTone(severity: FindingSeverity | RiskLevel) {
  if (severity === "critical" || severity === "error" || severity === "high") {
    return "danger" as const;
  }

  if (severity === "warning" || severity === "medium") {
    return "warning" as const;
  }

  if (severity === "low" || severity === "info") {
    return "info" as const;
  }

  return "neutral" as const;
}

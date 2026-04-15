import type { ChangeEvent } from "react";

import type { CaseStatus } from "@/api/contracts";

interface CaseFiltersProps {
  searchValue: string;
  onSearchChange: (value: string) => void;
  status: "all" | CaseStatus;
  onStatusChange: (value: "all" | CaseStatus) => void;
  manualReviewOnly: boolean;
  onManualReviewOnlyChange: (value: boolean) => void;
}

const statusOptions: Array<{ value: "all" | CaseStatus; label: string }> = [
  { value: "all", label: "All statuses" },
  { value: "created", label: "Created" },
  { value: "documents_uploaded", label: "Documents uploaded" },
  { value: "processing", label: "Processing" },
  { value: "validation_completed", label: "Validation completed" },
  { value: "manual_review_required", label: "Manual review required" },
  { value: "decision_ready", label: "Decision ready" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "failed", label: "Failed" },
];

export function CaseFilters({
  searchValue,
  onSearchChange,
  status,
  onStatusChange,
  manualReviewOnly,
  onManualReviewOnlyChange,
}: CaseFiltersProps) {
  function handleSearchChange(event: ChangeEvent<HTMLInputElement>) {
    onSearchChange(event.target.value);
  }

  function handleStatusChange(event: ChangeEvent<HTMLSelectElement>) {
    onStatusChange(event.target.value as "all" | CaseStatus);
  }

  function handleManualReviewChange(event: ChangeEvent<HTMLInputElement>) {
    onManualReviewOnlyChange(event.target.checked);
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_220px_220px]">
      <label className="block">
        <span className="eyebrow">Search</span>
        <input
          value={searchValue}
          onChange={handleSearchChange}
          placeholder="Search by case reference or UUID"
          className="mt-2 w-full rounded-xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none ring-accent transition focus:ring-2"
        />
      </label>

      <label className="block">
        <span className="eyebrow">Status</span>
        <select
          value={status}
          onChange={handleStatusChange}
          className="mt-2 w-full rounded-xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none ring-accent transition focus:ring-2"
        >
          {statusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label className="flex items-end">
        <span className="flex w-full items-center gap-3 rounded-xl border border-line bg-white px-4 py-3">
          <input
            type="checkbox"
            checked={manualReviewOnly}
            onChange={handleManualReviewChange}
            className="h-4 w-4 rounded border-line text-accent focus:ring-accent"
          />
          <span className="text-sm font-medium text-ink">Manual review only</span>
        </span>
      </label>
    </div>
  );
}

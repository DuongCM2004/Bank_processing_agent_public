import type { CaseStatus } from "@/types/api";
import { humanize } from "@/utils/format";

const statuses: Array<"all" | CaseStatus> = [
  "all",
  "processing",
  "validation_completed",
  "manual_review_required",
  "decision_ready",
  "approved",
  "rejected",
  "failed",
];

interface CaseFiltersProps {
  searchValue: string;
  status: "all" | CaseStatus;
  manualReviewOnly: boolean;
  onSearchChange: (value: string) => void;
  onStatusChange: (value: "all" | CaseStatus) => void;
  onManualReviewOnlyChange: (value: boolean) => void;
}

export function CaseFilters({
  searchValue,
  status,
  manualReviewOnly,
  onSearchChange,
  onStatusChange,
  onManualReviewOnlyChange,
}: CaseFiltersProps) {
  return (
    <div className="grid gap-3 md:grid-cols-[minmax(240px,1fr)_220px_auto] md:items-end">
      <label className="block text-sm font-semibold text-ink">
        Search case
        <input
          className="mt-2 w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none focus:border-teal focus:ring-4 focus:ring-teal/10"
          value={searchValue}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Case reference or id"
        />
      </label>
      <label className="block text-sm font-semibold text-ink">
        Status
        <select
          className="mt-2 w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none focus:border-teal focus:ring-4 focus:ring-teal/10"
          value={status}
          onChange={(event) => onStatusChange(event.target.value as "all" | CaseStatus)}
        >
          {statuses.map((item) => (
            <option key={item} value={item}>
              {humanize(item)}
            </option>
          ))}
        </select>
      </label>
      <label className="flex min-h-10 items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-semibold text-ink">
        <input
          type="checkbox"
          className="h-4 w-4 rounded border-line text-teal focus:ring-teal"
          checked={manualReviewOnly}
          onChange={(event) => onManualReviewOnlyChange(event.target.checked)}
        />
        Manual review only
      </label>
    </div>
  );
}

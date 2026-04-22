import { Button } from "@/components/ui/Button";

interface CasePaginationControlsProps {
  page: number;
  total: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export function CasePaginationControls({ page, total, pageSize, onPageChange }: CasePaginationControlsProps) {
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const startRow = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const endRow = Math.min(page * pageSize, total);

  return (
    <div className="flex flex-col gap-3 border-t border-line pt-4 md:flex-row md:items-center md:justify-between">
      <p className="text-sm text-slate">
        Showing <span className="font-semibold text-ink">{startRow}</span> to <span className="font-semibold text-ink">{endRow}</span> of{" "}
        <span className="font-semibold text-ink">{total}</span> cases
      </p>

      <div className="flex items-center gap-3">
        <span className="text-sm text-slate">
          Page <span className="font-semibold text-ink">{page}</span> of <span className="font-semibold text-ink">{pageCount}</span>
        </span>
        <Button type="button" variant="secondary" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
          Previous
        </Button>
        <Button type="button" variant="secondary" disabled={page >= pageCount} onClick={() => onPageChange(page + 1)}>
          Next
        </Button>
      </div>
    </div>
  );
}

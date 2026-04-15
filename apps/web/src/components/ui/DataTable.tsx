import type { ReactNode } from "react";

interface Column<T> {
  key: string;
  header: string;
  cell: (item: T) => ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  getRowId: (item: T) => string;
}

export function DataTable<T>({ columns, rows, getRowId }: DataTableProps<T>) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse">
        <thead>
          <tr className="border-b border-line text-left">
            {columns.map((column) => (
              <th key={column.key} className={`pb-3 text-xs font-semibold uppercase tracking-wide text-slate ${column.className ?? ""}`}>
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={getRowId(row)} className="border-b border-line/70 align-top last:border-b-0">
              {columns.map((column) => (
                <td key={column.key} className={`py-4 pr-4 text-sm text-ink ${column.className ?? ""}`}>
                  {column.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

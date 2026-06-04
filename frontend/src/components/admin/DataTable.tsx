"use client";

import Link from "next/link";
import { type ReactNode } from "react";

export type SortDirection = "asc" | "desc";

export interface Column<T> {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (row: T) => ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  loading?: boolean;
  sortKey?: string;
  sortDirection?: SortDirection;
  onSortChange?: (key: string, direction: SortDirection) => void;
  rowHref?: (row: T) => string;
  keyField?: keyof T;
  emptyState?: ReactNode;
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  rows,
  loading = false,
  sortKey,
  sortDirection,
  onSortChange,
  rowHref,
  keyField = "id" as keyof T,
  emptyState,
}: DataTableProps<T>) {
  function handleHeaderClick(column: Column<T>) {
    if (!column.sortable || !onSortChange) return;
    const nextDirection: SortDirection =
      sortKey === column.key && sortDirection === "asc" ? "desc" : "asc";
    onSortChange(column.key, nextDirection);
  }

  if (loading) {
    return (
      <div className="space-y-2">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="h-12 rounded-md bg-zinc-100 animate-pulse dark:bg-zinc-800"
          />
        ))}
      </div>
    );
  }

  if (rows.length === 0 && emptyState) {
    return <>{emptyState}</>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
      <table className="w-full text-sm">
        <thead className="bg-zinc-50 text-left dark:bg-zinc-900">
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={`px-4 py-2 font-medium ${
                  col.sortable ? "cursor-pointer select-none" : ""
                }`}
                onClick={() => handleHeaderClick(col)}
              >
                {col.label}
                {col.sortable && sortKey === col.key && (
                  <span className="ml-1 text-xs">
                    {sortDirection === "asc" ? "↑" : "↓"}
                  </span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const key = row[keyField] as string | number;
            const href = rowHref?.(row);
            return (
              <tr
                key={key}
                className="border-t border-zinc-200 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
              >
                {columns.map((col) => {
                  const content = col.render
                    ? col.render(row)
                    : (row[col.key] as ReactNode);
                  return (
                    <td key={col.key} className="px-4 py-2">
                      {href && col === columns[0] ? (
                        <Link href={href} className="hover:underline">
                          {content}
                        </Link>
                      ) : (
                        content
                      )}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

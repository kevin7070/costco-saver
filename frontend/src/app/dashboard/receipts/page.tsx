"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  DataTable,
  EmptyState,
  PageHeader,
  type Column,
  type SortDirection,
} from "@/components/admin";
import { useApi } from "@/hooks/useApi";

type Receipt = {
  id: string;
  store_location: string;
  purchase_date: string | null;
  receipt_number: string;
  parse_status: string;
  created_at: string;
};

type Paginated = { count: number; results: Receipt[] };

const STATUS_STYLES: Record<string, string> = {
  queued: "bg-zinc-500/10 text-zinc-500",
  processing: "bg-blue-500/10 text-blue-500",
  needs_review: "bg-amber-500/10 text-amber-600",
  confirmed: "bg-green-500/10 text-green-600",
  failed: "bg-red-500/10 text-red-500",
};

function StatusBadge({ status }: { status: string }) {
  const cls = STATUS_STYLES[status] ?? "bg-zinc-500/10 text-zinc-500";
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${cls}`}>
      {status.replace("_", " ")}
    </span>
  );
}

export default function ReceiptsListPage() {
  const { fetchApi } = useApi();
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [sortKey, setSortKey] = useState("created_at");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      try {
        const ordering = `${sortDirection === "desc" ? "-" : ""}${sortKey}`;
        const data = await fetchApi<Paginated>(`/receipts/?ordering=${ordering}`, { signal });
        setReceipts(data.results);
      } catch (err) {
        if (err instanceof Error && err.name !== "AbortError") setError(err.message);
      } finally {
        setLoading(false);
      }
    },
    [fetchApi, sortKey, sortDirection],
  );

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const columns: Column<Receipt>[] = [
    { key: "store_location", label: "Store", render: (r) => r.store_location || "—" },
    { key: "purchase_date", label: "Purchased", sortable: true, render: (r) => r.purchase_date ?? "—" },
    { key: "parse_status", label: "Status", render: (r) => <StatusBadge status={r.parse_status} /> },
    {
      key: "created_at",
      label: "Uploaded",
      sortable: true,
      render: (r) => new Date(r.created_at).toLocaleDateString(),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Receipts"
        breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Receipts" }]}
        actions={
          <Link
            href="/dashboard/receipts/new"
            className="rounded-md bg-zinc-900 px-3 py-1.5 text-sm text-white dark:bg-white dark:text-zinc-900"
          >
            Upload receipt
          </Link>
        }
      />

      {error && (
        <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-500">
          {error}
        </div>
      )}

      <DataTable
        columns={columns}
        rows={receipts}
        loading={loading}
        sortKey={sortKey}
        sortDirection={sortDirection}
        onSortChange={(key, direction) => {
          setSortKey(key);
          setSortDirection(direction);
        }}
        rowHref={(r) => `/dashboard/receipts/${r.id}`}
        emptyState={
          <EmptyState
            title="No receipts yet"
            description="Upload your first Costco receipt to start tracking."
            action={
              <Link
                href="/dashboard/receipts/new"
                className="inline-block rounded-md bg-zinc-900 px-3 py-1.5 text-sm text-white dark:bg-white dark:text-zinc-900"
              >
                Upload receipt
              </Link>
            }
          />
        }
      />
    </div>
  );
}

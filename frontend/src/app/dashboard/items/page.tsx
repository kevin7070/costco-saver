"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  DataTable,
  EmptyState,
  FilterBar,
  ItemStatusBadge,
  PageHeader,
  type Column,
  type ItemStatus,
  type SortDirection,
} from "@/components/admin";
import { useApi } from "@/hooks/useApi";

type Item = {
  id: number;
  name: string;
  description: string;
  status: ItemStatus;
  owner_name: string;
  created_at: string;
};

type PaginatedItems = {
  count: number;
  results: Item[];
};

export default function ItemsListPage() {
  const { fetchApi } = useApi();
  const [items, setItems] = useState<Item[]>([]);
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState("created_at");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadItems = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      try {
        const ordering = `${sortDirection === "desc" ? "-" : ""}${sortKey}`;
        const params = new URLSearchParams({ ordering });
        if (search) params.set("search", search);
        const data = await fetchApi<PaginatedItems>(
          `/items/?${params.toString()}`,
          { signal },
        );
        setItems(data.results);
      } catch (err) {
        if (err instanceof Error && err.name !== "AbortError") {
          setError(err.message);
        }
      } finally {
        setLoading(false);
      }
    },
    [fetchApi, search, sortKey, sortDirection],
  );

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => loadItems(controller.signal), 300);
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [loadItems]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const columns: Column<Item>[] = [
    {
      key: "name",
      label: "Name",
      sortable: true,
    },
    {
      key: "status",
      label: "Status",
      render: (row) => <ItemStatusBadge status={row.status} />,
    },
    {
      key: "created_at",
      label: "Created",
      sortable: true,
      render: (row) => new Date(row.created_at).toLocaleDateString(),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Items"
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Items" },
        ]}
        actions={
          <Link
            href="/dashboard/items/new"
            className="rounded-md bg-zinc-900 px-3 py-1.5 text-sm text-white dark:bg-white dark:text-zinc-900"
          >
            New item
          </Link>
        }
      />

      {error && (
        <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-500">
          {error}
        </div>
      )}

      <FilterBar
        search={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search items…"
        hasActiveFilters={!!search}
        onClear={() => setSearch("")}
      />

      <DataTable
        columns={columns}
        rows={items}
        loading={loading}
        sortKey={sortKey}
        sortDirection={sortDirection}
        onSortChange={(key, direction) => {
          setSortKey(key);
          setSortDirection(direction);
        }}
        rowHref={(row) => `/dashboard/items/${row.id}`}
        emptyState={
          <EmptyState
            title={search ? "No items match your search" : "No items yet"}
            description={
              search
                ? "Try a different search term or clear filters."
                : "Create your first item to get started."
            }
            action={
              !search && (
                <Link
                  href="/dashboard/items/new"
                  className="inline-block rounded-md bg-zinc-900 px-3 py-1.5 text-sm text-white dark:bg-white dark:text-zinc-900"
                >
                  New item
                </Link>
              )
            }
          />
        }
      />
    </div>
  );
}

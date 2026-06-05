"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  ConfirmDialog,
  ItemStatusBadge,
  PageHeader,
  type ItemStatus,
} from "@/components/admin";
import { ApiError, useApi } from "@/hooks/useApi";

type Item = {
  id: string;
  name: string;
  description: string;
  status: ItemStatus;
  owner: string;
  owner_name: string;
  created_at: string;
  updated_at: string;
};

export default function ItemDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { fetchApi } = useApi();
  const [item, setItem] = useState<Item | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showArchive, setShowArchive] = useState(false);
  const [archiving, setArchiving] = useState(false);

  const itemId = params?.id;

  const loadItem = useCallback(async () => {
    if (!itemId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchApi<Item>(`/items/${itemId}/`);
      setItem(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load item");
    } finally {
      setLoading(false);
    }
  }, [fetchApi, itemId]);

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    loadItem();
  }, [loadItem]);
  /* eslint-enable react-hooks/set-state-in-effect */

  async function handleArchive() {
    if (!itemId) return;
    setArchiving(true);
    try {
      await fetchApi(`/items/${itemId}/archive/`, { method: "POST" });
      setShowArchive(false);
      await loadItem();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to archive");
      setShowArchive(false);
    } finally {
      setArchiving(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-64 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800" />
        <div className="h-40 animate-pulse rounded-lg bg-zinc-200 dark:bg-zinc-800" />
      </div>
    );
  }

  if (error && !item) {
    return (
      <div className="rounded-md border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-500">
        {error}
      </div>
    );
  }

  if (!item) return null;

  return (
    <div>
      <PageHeader
        title={item.name}
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Items", href: "/dashboard/items" },
          { label: item.name },
        ]}
        actions={
          <>
            <button
              type="button"
              onClick={() => router.back()}
              className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm dark:border-zinc-700"
            >
              Back
            </button>
            {item.status === "active" && (
              <button
                type="button"
                onClick={() => setShowArchive(true)}
                className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm dark:border-zinc-700"
              >
                Archive
              </button>
            )}
          </>
        }
      />

      {error && (
        <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-500">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <section className="rounded-lg border border-zinc-200 p-5 lg:col-span-2 dark:border-zinc-800">
          <div className="mb-4 flex items-center gap-3">
            <ItemStatusBadge status={item.status} />
          </div>
          <h2 className="mb-2 font-semibold">Description</h2>
          <p className="whitespace-pre-wrap text-sm text-zinc-700 dark:text-zinc-300">
            {item.description || "—"}
          </p>
        </section>
        <aside className="space-y-3 text-sm">
          <div className="rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
            <p className="text-xs uppercase text-zinc-500">Owner</p>
            <p className="font-medium">{item.owner_name}</p>
          </div>
          <div className="rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
            <p className="text-xs uppercase text-zinc-500">Created</p>
            <p className="font-medium">
              {new Date(item.created_at).toLocaleString()}
            </p>
          </div>
          <div className="rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
            <p className="text-xs uppercase text-zinc-500">Updated</p>
            <p className="font-medium">
              {new Date(item.updated_at).toLocaleString()}
            </p>
          </div>
        </aside>
      </div>

      <ConfirmDialog
        open={showArchive}
        onClose={() => setShowArchive(false)}
        onConfirm={handleArchive}
        title="Archive this item?"
        description="Archived items are hidden from the default view. You can restore via Django admin."
        confirmLabel="Archive"
        variant="warning"
        loading={archiving}
      />
    </div>
  );
}

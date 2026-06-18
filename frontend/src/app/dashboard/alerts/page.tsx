"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  EmptyState,
  PageHeader,
  StatusBadge,
  type BadgeVariant,
} from "@/components/admin";
import { Button } from "@/components/ui/catalyst/button";
import { useApi } from "@/hooks/useApi";

type AlertStatus = "open" | "seen" | "actioned" | "dismissed";

type Product = {
  id: string;
  item_number: string;
  name: string;
  url: string;
  current_price: string | null;
  on_sale: boolean;
};

type PriceAlert = {
  id: string;
  status: AlertStatus;
  observed_price: string;
  purchase_price: string;
  delta: string;
  within_adjustment_window: boolean;
  created_at: string;
  updated_at: string;
  product: Product | null;
  item_name: string;
  store_location: string | null;
  purchase_date: string | null;
};

type Paginated = { count: number; results: PriceAlert[] };

const TABS = [
  { key: "open", label: "Open" },
  { key: "seen", label: "Seen" },
  { key: "actioned", label: "Actioned" },
  { key: "dismissed", label: "Dismissed" },
  { key: "all", label: "All" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

const ALERT_BADGE: Record<AlertStatus, { variant: BadgeVariant; label: string }> = {
  open: { variant: "warning", label: "Open" },
  seen: { variant: "info", label: "Seen" },
  actioned: { variant: "success", label: "Actioned" },
  dismissed: { variant: "muted", label: "Dismissed" },
};

function fmt(amount: string) {
  return `$${Number(amount).toFixed(2)}`;
}

function AlertCard({
  alert,
  onAction,
}: {
  alert: PriceAlert;
  onAction: (id: string, action: string) => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);

  const act = async (action: string) => {
    setBusy(true);
    try {
      await onAction(alert.id, action);
    } finally {
      setBusy(false);
    }
  };

  const badge = ALERT_BADGE[alert.status];
  const productName = alert.product?.name || alert.item_name;
  const canAct = alert.status !== "dismissed";

  return (
    <div className="flex flex-col rounded-lg border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
      {/* Header: name + status */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-medium leading-snug">{productName}</h3>
          {alert.product?.item_number && (
            <p className="mt-0.5 text-xs text-zinc-500">
              Item #{alert.product.item_number}
            </p>
          )}
        </div>
        <StatusBadge variant={badge.variant}>{badge.label}</StatusBadge>
      </div>

      {/* Price comparison */}
      <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm">
        <span className="text-zinc-500">Paid</span>
        <span className="font-semibold">{fmt(alert.purchase_price)}</span>
        <span className="text-zinc-400">→</span>
        <span className="text-zinc-500">Now</span>
        <span className="font-semibold text-green-600 dark:text-green-400">
          {fmt(alert.observed_price)}
        </span>
        <span className="font-semibold text-green-600 dark:text-green-400">
          Save {fmt(alert.delta)}
        </span>
      </div>

      {/* Window badge */}
      <div className="mt-2">
        {alert.within_adjustment_window ? (
          <StatusBadge variant="success">Within adjustment window</StatusBadge>
        ) : (
          <StatusBadge variant="muted">Outside adjustment window</StatusBadge>
        )}
      </div>

      {/* Context row */}
      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-zinc-500">
        {alert.store_location && <span>{alert.store_location}</span>}
        {alert.purchase_date && (
          <span>{new Date(alert.purchase_date).toLocaleDateString()}</span>
        )}
        {alert.product?.url && (
          <Link
            href={alert.product.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-500 hover:underline"
          >
            View on Costco ↗
          </Link>
        )}
      </div>

      {/* Actions */}
      {canAct && (
        <div className="mt-4 flex flex-wrap gap-2">
          {alert.status === "open" && (
            <Button
              outline
              type="button"
              disabled={busy}
              onClick={() => act("mark-seen")}
            >
              Mark seen
            </Button>
          )}
          {(alert.status === "open" || alert.status === "seen") && (
            <Button
              color="green"
              type="button"
              disabled={busy}
              onClick={() => act("mark-actioned")}
            >
              Mark actioned
            </Button>
          )}
          <Button
            plain
            type="button"
            disabled={busy}
            onClick={() => act("dismiss")}
          >
            Dismiss
          </Button>
        </div>
      )}
    </div>
  );
}

export default function AlertsPage() {
  const { fetchApi } = useApi();
  const [alerts, setAlerts] = useState<PriceAlert[]>([]);
  const [tab, setTab] = useState<TabKey>("open");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      try {
        const query = tab === "all" ? "" : `?status=${tab}`;
        const data = await fetchApi<Paginated>(`/alerts/${query}`, { signal });
        setAlerts(data.results);
      } catch (err) {
        if (err instanceof Error && err.name !== "AbortError") {
          setError(err.message);
        }
      } finally {
        setLoading(false);
      }
    },
    [fetchApi, tab],
  );

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const handleAction = useCallback(
    async (id: string, action: string) => {
      await fetchApi(`/alerts/${id}/${action}/`, { method: "POST" });
      await load();
    },
    [fetchApi, load],
  );

  return (
    <div>
      <PageHeader
        title="Price Alerts"
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Price Alerts" },
        ]}
      />

      {/* Status filter tabs */}
      <div className="mb-6 flex border-b border-zinc-200 dark:border-zinc-800">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              tab === t.key
                ? "border-b-2 border-zinc-900 text-zinc-900 dark:border-white dark:text-white"
                : "text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-500">
          {error}
        </div>
      )}

      {loading ? (
        <div className="p-4 text-sm text-zinc-500">Loading…</div>
      ) : alerts.length === 0 ? (
        <EmptyState
          title="No alerts"
          description={
            tab === "open"
              ? "No open price drops right now. Alerts appear when a receipt item drops in price after you bought it."
              : "No alerts match this filter."
          }
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {alerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} onAction={handleAction} />
          ))}
        </div>
      )}
    </div>
  );
}

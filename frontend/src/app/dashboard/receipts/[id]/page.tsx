"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/admin";
import { ApiError, useApi } from "@/hooks/useApi";

type LineItem = {
  id?: string;
  raw_name: string;
  item_number: string;
  quantity: number;
  unit_price: string | null;
  amount: string | null;
  item_type: "product" | "service" | "discount";
  taxable: boolean;
  tracking_status?: string;
};

type Receipt = {
  id: string;
  image: string;
  store_location: string;
  store_number: string;
  purchase_date: string | null;
  receipt_number: string;
  invoice_number: string;
  parse_status: string;
  parse_error: string;
  line_items: LineItem[];
};

type Header = {
  store_location: string;
  store_number: string;
  purchase_date: string;
  receipt_number: string;
  invoice_number: string;
};

export default function ReceiptDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const { fetchApi } = useApi();

  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [items, setItems] = useState<LineItem[]>([]);
  const [header, setHeader] = useState<Header>({
    store_location: "",
    store_number: "",
    purchase_date: "",
    receipt_number: "",
    invoice_number: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetchApi<Receipt>(`/receipts/${id}/`);
      setReceipt(r);
      setItems(r.line_items.map((li) => ({ ...li })));
      setHeader({
        store_location: r.store_location,
        store_number: r.store_number,
        purchase_date: r.purchase_date ?? "",
        receipt_number: r.receipt_number,
        invoice_number: r.invoice_number,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load receipt");
    } finally {
      setLoading(false);
    }
  }, [fetchApi, id]);

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    load();
  }, [load]);
  /* eslint-enable react-hooks/set-state-in-effect */

  function updateItem(i: number, patch: Partial<LineItem>) {
    setItems((prev) => prev.map((it, idx) => (idx === i ? { ...it, ...patch } : it)));
  }
  function removeItem(i: number) {
    setItems((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function confirm() {
    setSaving(true);
    setError(null);
    try {
      const payload = {
        ...header,
        purchase_date: header.purchase_date || null,
        line_items: items.map((it) => ({
          raw_name: it.raw_name,
          item_number: it.item_number,
          quantity: it.quantity,
          unit_price: it.unit_price || null,
          amount: it.amount || null,
          item_type: it.item_type,
          taxable: it.taxable,
        })),
      };
      await fetchApi(`/receipts/${id}/confirm/`, { method: "POST", body: payload });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to confirm");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="p-4 text-sm text-zinc-500">Loading…</div>;
  if (!receipt) return <div className="p-4 text-sm text-red-500">{error ?? "Not found"}</div>;

  const editable = receipt.parse_status === "needs_review";
  const pending = ["queued", "processing"].includes(receipt.parse_status);

  return (
    <div>
      <PageHeader
        title="Receipt"
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Receipts", href: "/dashboard/receipts" },
          { label: `#${receipt.id}` },
        ]}
      />

      {error && (
        <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-500">
          {error}
        </div>
      )}
      {pending && (
        <div className="mb-4 rounded-md border border-blue-500/20 bg-blue-500/10 p-3 text-sm text-blue-600">
          Still reading this receipt… refresh in a moment.
        </div>
      )}
      {receipt.parse_status === "failed" && (
        <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-500">
          Couldn&apos;t read this receipt. {receipt.parse_error}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {/* Receipt image — for in-store retrieval (barcode visible) */}
        <div>
          {receipt.image && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={receipt.image}
              alt="Receipt"
              className="w-full rounded-lg border border-zinc-200 dark:border-zinc-800"
            />
          )}
          {receipt.receipt_number && (
            <div className="mt-3 rounded-lg border border-zinc-200 p-3 text-center dark:border-zinc-800">
              <div className="text-xs text-zinc-500">Receipt # (show at returns)</div>
              <div className="font-mono text-lg tracking-wide break-all">
                {receipt.receipt_number}
              </div>
            </div>
          )}
        </div>

        {/* Details + review */}
        <div>
          {editable && (
            <p className="mb-3 text-sm text-amber-600">
              Reading isn&apos;t perfect — please check and fix anything below, then confirm.
            </p>
          )}

          <div className="mb-4 grid grid-cols-2 gap-3">
            <Field label="Store" value={header.store_location} editable={editable} onChange={(v) => setHeader({ ...header, store_location: v })} />
            <Field label="Purchase date" value={header.purchase_date} editable={editable} onChange={(v) => setHeader({ ...header, purchase_date: v })} placeholder="YYYY-MM-DD" />
            <Field label="Receipt #" value={header.receipt_number} editable={editable} onChange={(v) => setHeader({ ...header, receipt_number: v })} />
            <Field label="Invoice #" value={header.invoice_number} editable={editable} onChange={(v) => setHeader({ ...header, invoice_number: v })} />
          </div>

          <div className="space-y-2">
            {items.map((it, i) => (
              <div key={i} className="rounded-md border border-zinc-200 p-2 text-sm dark:border-zinc-800">
                {editable ? (
                  <div className="grid grid-cols-12 items-center gap-2">
                    <input className="col-span-5 rounded border border-zinc-300 px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900" value={it.raw_name} onChange={(e) => updateItem(i, { raw_name: e.target.value })} placeholder="Name" />
                    <input className="col-span-3 rounded border border-zinc-300 px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900" value={it.item_number} onChange={(e) => updateItem(i, { item_number: e.target.value })} placeholder="Item #" />
                    <input className="col-span-2 rounded border border-zinc-300 px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900" value={it.amount ?? ""} onChange={(e) => updateItem(i, { amount: e.target.value })} placeholder="$" />
                    <select className="col-span-1 rounded border border-zinc-300 px-1 py-1 dark:border-zinc-700 dark:bg-zinc-900" value={it.item_type} onChange={(e) => updateItem(i, { item_type: e.target.value as LineItem["item_type"] })}>
                      <option value="product">P</option>
                      <option value="service">S</option>
                      <option value="discount">D</option>
                    </select>
                    <button type="button" onClick={() => removeItem(i)} className="col-span-1 text-red-500" aria-label="Remove">
                      ✕
                    </button>
                  </div>
                ) : (
                  <div className="flex justify-between">
                    <span>
                      {it.raw_name}
                      {it.item_number && <span className="text-zinc-400"> ({it.item_number})</span>}
                    </span>
                    <span className={it.item_type === "discount" ? "text-green-600" : ""}>{it.amount}</span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {editable && (
            <div className="mt-4">
              <button
                type="button"
                onClick={confirm}
                disabled={saving}
                className="rounded-md bg-zinc-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-white dark:text-zinc-900"
              >
                {saving ? "Saving…" : "Confirm receipt"}
              </button>
            </div>
          )}
          {receipt.parse_status === "confirmed" && (
            <p className="mt-3 text-sm text-green-600">✓ Confirmed</p>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  editable,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  editable: boolean;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div>
      <div className="text-xs text-zinc-500">{label}</div>
      {editable ? (
        <input
          className="mt-0.5 block w-full rounded border border-zinc-300 px-2 py-1 text-sm dark:border-zinc-700 dark:bg-zinc-900"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
        />
      ) : (
        <div className="mt-0.5 text-sm">{value || "—"}</div>
      )}
    </div>
  );
}

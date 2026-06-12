"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { PageHeader } from "@/components/admin";
import { Button } from "@/components/ui/catalyst/button";

export default function UploadReceiptPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!file) {
      setError("Please choose a receipt image or PDF.");
      return;
    }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("image", file);
      // FormData upload: do NOT set Content-Type — the browser adds the
      // multipart boundary itself. (useApi is JSON-only, so we fetch directly.)
      const resp = await fetch("/api/v1/receipts/", {
        method: "POST",
        body: fd,
        credentials: "include",
      });
      const data = (await resp.json().catch(() => ({}))) as {
        id?: string;
        detail?: string;
        image?: string[];
      };
      if (!resp.ok) {
        throw new Error(data.detail ?? data.image?.[0] ?? `Upload failed (HTTP ${resp.status})`);
      }
      router.push(`/dashboard/receipts/${data.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Upload receipt"
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Receipts", href: "/dashboard/receipts" },
          { label: "Upload" },
        ]}
      />

      {error && (
        <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-500">
          {error}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="max-w-lg rounded-lg border border-zinc-200 p-6 dark:border-zinc-800"
      >
        <label htmlFor="file" className="mb-1 block text-sm font-medium">
          Receipt image or PDF
        </label>
        <input
          id="file"
          type="file"
          accept="image/*,application/pdf"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          required
          className="mb-2 block w-full text-sm"
        />
        <p className="mb-6 text-xs text-zinc-500">
          We&apos;ll read it automatically — you can review and fix anything after.
        </p>

        <div className="flex gap-3">
          <Button outline type="button" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button type="submit" disabled={uploading}>
            {uploading ? "Uploading…" : "Upload"}
          </Button>
        </div>
      </form>
    </div>
  );
}

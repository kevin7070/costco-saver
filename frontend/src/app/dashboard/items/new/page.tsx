"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { PageHeader } from "@/components/admin";
import { Button } from "@/components/ui/catalyst/button";
import { Field, Label } from "@/components/ui/catalyst/fieldset";
import { Input } from "@/components/ui/catalyst/input";
import { Textarea } from "@/components/ui/catalyst/textarea";
import { ApiError, useApi } from "@/hooks/useApi";
import { itemCreateSchema } from "@/lib/validation";

export default function NewItemPage() {
  const router = useRouter();
  const { fetchApi } = useApi();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const parsed = itemCreateSchema.safeParse({ name, description });
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Invalid input");
      return;
    }

    setSaving(true);
    try {
      const created = await fetchApi<{ id: string }>("/items/", {
        method: "POST",
        body: parsed.data,
      });
      router.push(`/dashboard/items/${created.id}`);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to create item",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="New item"
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Items", href: "/dashboard/items" },
          { label: "New" },
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
        <div className="space-y-4">
          <Field>
            <Label>Name</Label>
            <Input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </Field>

          <Field>
            <Label>Description</Label>
            <Textarea
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </Field>
        </div>

        <div className="mt-6 flex gap-3">
          <Button outline type="button" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            {saving ? "Creating…" : "Create"}
          </Button>
        </div>
      </form>
    </div>
  );
}

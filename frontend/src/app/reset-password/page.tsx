"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useApi, ApiError } from "@/hooks/useApi";
import { resetPasswordSchema } from "@/lib/validation";

const inputClass =
  "block w-full rounded-md border border-zinc-300 px-3 py-2 outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 dark:border-zinc-700 dark:bg-zinc-900";

function ResetPasswordInner() {
  const { fetchApi } = useApi();
  const params = useSearchParams();
  const uid = params.get("uid") ?? "";
  const token = params.get("token") ?? "";
  const [form, setForm] = useState({ new_password: "", confirm_password: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  function update(field: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const parsed = resetPasswordSchema.safeParse(form);
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Invalid input");
      return;
    }
    if (!uid || !token) {
      setError("Invalid or expired reset link.");
      return;
    }
    setLoading(true);
    try {
      await fetchApi("/auth/reset-password/", {
        method: "POST",
        body: { uid, token, new_password: parsed.data.new_password },
      });
      setDone(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Network error");
    } finally {
      setLoading(false);
    }
  }

  if (done) {
    return (
      <div className="w-full max-w-sm rounded-lg border border-zinc-200 p-6 text-center dark:border-zinc-800">
        <h1 className="mb-2 text-2xl font-semibold">Password reset</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Your password has been updated. You can now log in.
        </p>
        <Link
          href="/login"
          className="mt-6 inline-block text-sm font-medium text-zinc-900 underline dark:text-white"
        >
          Log in
        </Link>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-sm rounded-lg border border-zinc-200 p-6 dark:border-zinc-800"
    >
      <h1 className="mb-6 text-2xl font-semibold">Choose a new password</h1>
      {error && (
        <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-500">
          {error}
        </div>
      )}
      <label className="mb-1 block text-sm" htmlFor="new_password">
        New password
      </label>
      <input
        id="new_password"
        type="password"
        value={form.new_password}
        onChange={update("new_password")}
        required
        className={`mb-1 ${inputClass}`}
      />
      <p className="mb-4 text-xs text-zinc-500">At least 8 characters.</p>
      <label className="mb-1 block text-sm" htmlFor="confirm_password">
        Confirm password
      </label>
      <input
        id="confirm_password"
        type="password"
        value={form.confirm_password}
        onChange={update("confirm_password")}
        required
        className={`mb-6 ${inputClass}`}
      />
      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-md bg-zinc-900 px-4 py-2 text-white outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 disabled:opacity-50 dark:bg-white dark:text-zinc-900"
      >
        {loading ? "Resetting…" : "Reset password"}
      </button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Suspense fallback={<p className="text-zinc-500">Loading…</p>}>
        <ResetPasswordInner />
      </Suspense>
    </main>
  );
}

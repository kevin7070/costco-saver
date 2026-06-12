"use client";

import Link from "next/link";
import { useState } from "react";

import { useApi, ApiError } from "@/hooks/useApi";
import { forgotPasswordSchema } from "@/lib/validation";
import { Button } from "@/components/ui/catalyst/button";
import { Field, Label } from "@/components/ui/catalyst/fieldset";
import { Input } from "@/components/ui/catalyst/input";

export default function ForgotPasswordPage() {
  const { fetchApi } = useApi();
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const parsed = forgotPasswordSchema.safeParse({ email });
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Invalid input");
      return;
    }
    setLoading(true);
    try {
      await fetchApi("/auth/forgot-password/", {
        method: "POST",
        body: parsed.data,
      });
      setSent(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Network error");
    } finally {
      setLoading(false);
    }
  }

  if (sent) {
    return (
      <main className="flex min-h-screen items-center justify-center p-6">
        <div className="w-full max-w-sm rounded-lg border border-zinc-200 p-6 text-center dark:border-zinc-800">
          <h1 className="mb-2 text-2xl font-semibold">Check your inbox</h1>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            If an account exists for <strong>{email}</strong>, a password reset
            link is on its way.
          </p>
          <Link
            href="/login"
            className="mt-6 inline-block text-sm font-medium text-zinc-900 underline dark:text-white"
          >
            Back to log in
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm rounded-lg border border-zinc-200 p-6 dark:border-zinc-800"
      >
        <h1 className="mb-1 text-2xl font-semibold">Forgot password</h1>
        <p className="mb-6 text-sm text-zinc-600 dark:text-zinc-400">
          Enter your email and we&apos;ll send a reset link.
        </p>
        {error && (
          <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-500">
            {error}
          </div>
        )}
        <div className="space-y-4">
          <Field>
            <Label>Email</Label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </Field>
        </div>
        <Button type="submit" disabled={loading} className="mt-6 w-full">
          {loading ? "Sending…" : "Send reset link"}
        </Button>
        <p className="mt-4 text-center text-sm text-zinc-600 dark:text-zinc-400">
          <Link
            href="/login"
            className="font-medium text-zinc-900 underline dark:text-white"
          >
            Back to log in
          </Link>
        </p>
      </form>
    </main>
  );
}

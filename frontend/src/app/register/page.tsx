"use client";

import Link from "next/link";
import { useState } from "react";

import { useApi, ApiError } from "@/hooks/useApi";
import { registerSchema } from "@/lib/validation";
import { Button } from "@/components/ui/catalyst/button";
import { Field, Label, Description } from "@/components/ui/catalyst/fieldset";
import { Input } from "@/components/ui/catalyst/input";

export default function RegisterPage() {
  const { fetchApi } = useApi();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    confirm_password: "",
    website: "", // honeypot
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  function update(field: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const parsed = registerSchema.safeParse(form);
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Invalid input");
      return;
    }
    setLoading(true);
    try {
      await fetchApi("/auth/register/", {
        method: "POST",
        body: {
          first_name: parsed.data.first_name,
          last_name: parsed.data.last_name,
          email: parsed.data.email,
          password: parsed.data.password,
          website: parsed.data.website,
        },
      });
      // Enumeration-safe: the API returns the same 202 whether the email is new
      // or existing. Show "check your inbox" either way; no auto-login.
      setSubmitted(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Network error");
    } finally {
      setLoading(false);
    }
  }

  if (submitted) {
    return (
      <main className="flex min-h-screen items-center justify-center p-6">
        <div className="w-full max-w-sm rounded-lg border border-zinc-200 p-6 text-center dark:border-zinc-800">
          <h1 className="mb-2 text-2xl font-semibold">Check your inbox</h1>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            If that email is new, we sent a verification link to{" "}
            <strong>{form.email}</strong>. Click it to activate your account, then
            log in.
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
        <h1 className="mb-1 text-2xl font-semibold">Create your account</h1>
        <p className="mb-6 text-sm text-zinc-600 dark:text-zinc-400">
          Start tracking your Costco purchases.
        </p>

        {error && (
          <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-500">
            {error}
          </div>
        )}

        {/* Honeypot: positioned off-screen; real users never fill it, bots do. */}
        <div aria-hidden="true" className="absolute left-[-9999px] top-[-9999px]">
          <label htmlFor="website">Website</label>
          <input
            id="website"
            type="text"
            tabIndex={-1}
            autoComplete="off"
            value={form.website}
            onChange={update("website")}
          />
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Field>
              <Label>First name</Label>
              <Input
                value={form.first_name}
                onChange={update("first_name")}
                required
              />
            </Field>
            <Field>
              <Label>Last name</Label>
              <Input
                value={form.last_name}
                onChange={update("last_name")}
                required
              />
            </Field>
          </div>

          <Field>
            <Label>Email</Label>
            <Input
              type="email"
              value={form.email}
              onChange={update("email")}
              required
              autoComplete="email"
            />
          </Field>

          <Field>
            <Label>Password</Label>
            <Input
              type="password"
              value={form.password}
              onChange={update("password")}
              required
              autoComplete="new-password"
            />
            <Description>At least 8 characters.</Description>
          </Field>

          <Field>
            <Label>Confirm password</Label>
            <Input
              type="password"
              value={form.confirm_password}
              onChange={update("confirm_password")}
              required
              autoComplete="new-password"
            />
          </Field>
        </div>

        <Button type="submit" disabled={loading} className="mt-6 w-full">
          {loading ? "Creating account..." : "Create account"}
        </Button>

        <p className="mt-4 text-center text-sm text-zinc-600 dark:text-zinc-400">
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-medium text-zinc-900 underline dark:text-white"
          >
            Log in
          </Link>
        </p>
      </form>
    </main>
  );
}

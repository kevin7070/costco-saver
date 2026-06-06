"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useApi, ApiError } from "@/hooks/useApi";
import { registerSchema } from "@/lib/validation";

const inputClass =
  "block w-full rounded-md border border-zinc-300 px-3 py-2 outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 dark:border-zinc-700 dark:bg-zinc-900";

export default function RegisterPage() {
  const router = useRouter();
  const { fetchApi } = useApi();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    confirm_password: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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
      // confirm_password is client-side only; send just what the API expects.
      await fetchApi("/auth/register/", {
        method: "POST",
        body: {
          first_name: parsed.data.first_name,
          last_name: parsed.data.last_name,
          email: parsed.data.email,
          password: parsed.data.password,
        },
      });
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Network error");
    } finally {
      setLoading(false);
    }
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

        <div className="mb-4 grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-sm" htmlFor="first_name">
              First name
            </label>
            <input
              id="first_name"
              value={form.first_name}
              onChange={update("first_name")}
              required
              className={inputClass}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm" htmlFor="last_name">
              Last name
            </label>
            <input
              id="last_name"
              value={form.last_name}
              onChange={update("last_name")}
              required
              className={inputClass}
            />
          </div>
        </div>

        <label className="mb-1 block text-sm" htmlFor="email">
          Email
        </label>
        <input
          id="email"
          type="email"
          value={form.email}
          onChange={update("email")}
          required
          className={`mb-4 ${inputClass}`}
        />

        <label className="mb-1 block text-sm" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          type="password"
          value={form.password}
          onChange={update("password")}
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
          {loading ? "Creating account..." : "Create account"}
        </button>

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

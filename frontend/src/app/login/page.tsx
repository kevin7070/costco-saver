"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/catalyst/button";
import { Field, Label } from "@/components/ui/catalyst/fieldset";
import { Input } from "@/components/ui/catalyst/input";
import { useApi, ApiError } from "@/hooks/useApi";
import { loginSchema } from "@/lib/validation";

export default function LoginPage() {
  const router = useRouter();
  const { fetchApi } = useApi();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [step, setStep] = useState<"creds" | "2fa">("creds");
  const [preAuth, setPreAuth] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleCreds(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const parsed = loginSchema.safeParse({ email, password });
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Invalid input");
      return;
    }
    setLoading(true);
    try {
      const data = await fetchApi<{
        requires_2fa?: boolean;
        pre_auth_token?: string;
      }>("/auth/login/", { method: "POST", body: parsed.data });
      if (data?.requires_2fa && data.pre_auth_token) {
        setPreAuth(data.pre_auth_token);
        setStep("2fa");
      } else {
        router.push("/dashboard");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Network error");
    } finally {
      setLoading(false);
    }
  }

  async function handle2fa(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await fetchApi("/auth/2fa/verify/", {
        method: "POST",
        body: { pre_auth_token: preAuth, code },
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
      {step === "creds" ? (
        <form
          onSubmit={handleCreds}
          className="w-full max-w-sm rounded-lg border border-zinc-200 p-6 dark:border-zinc-800"
        >
          <h1 className="mb-6 text-2xl font-semibold">Log in</h1>
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
            <Field>
              <Label>Password</Label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </Field>
          </div>
          <Button type="submit" disabled={loading} className="mt-6 w-full">
            {loading ? "Logging in..." : "Log in"}
          </Button>
          <p className="mt-4 text-center text-sm text-zinc-600 dark:text-zinc-400">
            <Link
              href="/forgot-password"
              className="font-medium text-zinc-900 underline dark:text-white"
            >
              Forgot password?
            </Link>
          </p>
          <p className="mt-2 text-center text-sm text-zinc-600 dark:text-zinc-400">
            Need an account?{" "}
            <Link
              href="/register"
              className="font-medium text-zinc-900 underline dark:text-white"
            >
              Sign up
            </Link>
          </p>
        </form>
      ) : (
        <form
          onSubmit={handle2fa}
          className="w-full max-w-sm rounded-lg border border-zinc-200 p-6 dark:border-zinc-800"
        >
          <h1 className="mb-1 text-2xl font-semibold">Two-factor code</h1>
          <p className="mb-6 text-sm text-zinc-600 dark:text-zinc-400">
            Enter the 6-digit code from your authenticator app.
          </p>
          {error && (
            <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-500">
              {error}
            </div>
          )}
          <Field>
            <Label>Code</Label>
            <Input
              inputMode="numeric"
              autoComplete="one-time-code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
          </Field>
          <Button type="submit" disabled={loading} className="mt-6 w-full">
            {loading ? "Verifying..." : "Verify"}
          </Button>
        </form>
      )}
    </main>
  );
}

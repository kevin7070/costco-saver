"use client";

import { useState } from "react";

import { Button } from "@/components/ui/catalyst/button";
import { Field, Label } from "@/components/ui/catalyst/fieldset";
import { Input } from "@/components/ui/catalyst/input";
import { useApi, ApiError } from "@/hooks/useApi";

export default function SecurityPage() {
  const { fetchApi } = useApi();
  const [otpauth, setOtpauth] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function startSetup() {
    setError(null);
    setMessage("");
    try {
      const data = await fetchApi<{ otpauth_url: string }>("/auth/2fa/setup/", {
        method: "POST",
      });
      setOtpauth(data.otpauth_url);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Network error");
    }
  }

  async function confirm(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await fetchApi("/auth/2fa/confirm/", { method: "POST", body: { code } });
      setMessage("Two-factor authentication enabled.");
      setOtpauth("");
      setCode("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Network error");
    }
  }

  async function disable(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await fetchApi("/auth/2fa/disable/", {
        method: "POST",
        body: { password },
      });
      setMessage("Two-factor authentication disabled.");
      setPassword("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Network error");
    }
  }

  return (
    <div className="max-w-lg">
      <h1 className="mb-6 text-2xl font-semibold">Security</h1>

      {error && (
        <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-500">
          {error}
        </div>
      )}
      {message && (
        <div className="mb-4 rounded-md border border-green-500/20 bg-green-500/10 p-3 text-sm text-green-600">
          {message}
        </div>
      )}

      <section className="mb-8 rounded-lg border border-zinc-200 p-6 dark:border-zinc-800">
        <h2 className="mb-2 text-lg font-medium">Two-factor authentication</h2>
        <p className="mb-4 text-sm text-zinc-600 dark:text-zinc-400">
          Add a TOTP authenticator app (e.g. Google Authenticator, 1Password) for
          a second login step.
        </p>

        {!otpauth ? (
          <Button type="button" onClick={startSetup}>
            Enable 2FA
          </Button>
        ) : (
          <form onSubmit={confirm}>
            <p className="mb-2 text-sm text-zinc-600 dark:text-zinc-400">
              Add this to your authenticator app, then enter the 6-digit code:
            </p>
            <code className="mb-4 block break-all rounded-md bg-zinc-100 p-3 text-xs dark:bg-zinc-900">
              {otpauth}
            </code>
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
            <Button type="submit" className="mt-4">
              Confirm
            </Button>
          </form>
        )}
      </section>

      <section className="rounded-lg border border-zinc-200 p-6 dark:border-zinc-800">
        <h2 className="mb-2 text-lg font-medium">Disable 2FA</h2>
        <form onSubmit={disable}>
          <Field>
            <Label>Confirm your password</Label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </Field>
          <Button color="red" type="submit" className="mt-4">
            Disable 2FA
          </Button>
        </form>
      </section>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { useApi, ApiError } from "@/hooks/useApi";

function VerifyEmailInner() {
  const { fetchApi } = useApi();
  const token = useSearchParams().get("token") ?? "";
  const [state, setState] = useState<"loading" | "ok" | "fail">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!token) {
        if (!cancelled) {
          setState("fail");
          setMessage("Missing verification token.");
        }
        return;
      }
      try {
        const r = await fetchApi<{ detail: string }>("/auth/verify-email/", {
          method: "POST",
          body: { token },
        });
        if (!cancelled) {
          setState("ok");
          setMessage(r.detail);
        }
      } catch (err) {
        if (!cancelled) {
          setState("fail");
          setMessage(
            err instanceof ApiError ? err.message : "Verification failed.",
          );
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, fetchApi]);

  const heading =
    state === "loading"
      ? "Verifying…"
      : state === "ok"
        ? "Email verified"
        : "Verification failed";

  return (
    <div className="w-full max-w-sm rounded-lg border border-zinc-200 p-6 text-center dark:border-zinc-800">
      <h1 className="mb-2 text-2xl font-semibold">{heading}</h1>
      <p className="text-sm text-zinc-600 dark:text-zinc-400">{message}</p>
      {state !== "loading" && (
        <Link
          href="/login"
          className="mt-6 inline-block text-sm font-medium text-zinc-900 underline dark:text-white"
        >
          {state === "ok" ? "Log in" : "Back to log in"}
        </Link>
      )}
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Suspense fallback={<p className="text-zinc-500">Verifying…</p>}>
        <VerifyEmailInner />
      </Suspense>
    </main>
  );
}

"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/catalyst/button";
import { useApi, ApiError } from "@/hooks/useApi";

// JWT access token TTL: 15 min. Refresh every 13 min proactively.
const REFRESH_INTERVAL_MS = 13 * 60 * 1000;
const VISIBILITY_REFRESH_COOLDOWN_MS = 30 * 1000;

type User = {
  id: string;
  email: string;
  full_name: string;
  user_type: string;
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { fetchApi } = useApi();
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);
  const lastRefreshRef = useRef<number>(0);

  const refresh = useCallback(async () => {
    try {
      await fetchApi("/auth/refresh/", { method: "POST" });
      lastRefreshRef.current = Date.now();
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.push("/login");
      }
      // Network error — ignore, retry next interval
    }
  }, [fetchApi, router]);

  const logout = useCallback(async () => {
    try {
      await fetchApi("/auth/logout/", { method: "POST" });
    } finally {
      router.push("/login");
    }
  }, [fetchApi, router]);

  // Initial auth check
  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const me = await fetchApi<User>("/auth/me/");
        if (!cancelled) setUser(me);
      } catch {
        if (!cancelled) router.push("/login");
      } finally {
        if (!cancelled) setChecking(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [fetchApi, router]);
  /* eslint-enable react-hooks/set-state-in-effect */

  // Interval refresh
  useEffect(() => {
    if (!user) return;
    const id = setInterval(refresh, REFRESH_INTERVAL_MS);
    return () => clearInterval(id);
  }, [user, refresh]);

  // Visibility refresh (tab focus)
  useEffect(() => {
    if (!user) return;
    const onVisibility = () => {
      if (document.visibilityState !== "visible") return;
      const elapsed = Date.now() - lastRefreshRef.current;
      if (elapsed < VISIBILITY_REFRESH_COOLDOWN_MS) return;
      refresh();
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, [user, refresh]);

  if (checking) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-zinc-500">Loading…</p>
      </main>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-6">
            <Link href="/dashboard" className="font-semibold">
              Dashboard
            </Link>
            <Link
              href="/dashboard/receipts"
              className="text-sm text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white"
            >
              Receipts
            </Link>
            <Link
              href="/dashboard/items"
              className="text-sm text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white"
            >
              Items
            </Link>
            <Link
              href="/dashboard/security"
              className="text-sm text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white"
            >
              Security
            </Link>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-zinc-600 dark:text-zinc-400">
              {user.full_name || user.email}
            </span>
            <Button outline type="button" onClick={logout}>
              Log out
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  );
}

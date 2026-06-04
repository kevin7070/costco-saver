import Link from "next/link";

export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Welcome</h1>
      <p className="text-zinc-600 dark:text-zinc-400 mb-6">
        This is a starter dashboard shell. Replace with your real landing page.
      </p>
      <div className="grid gap-4 md:grid-cols-2">
        <Link
          href="/dashboard/items"
          className="block rounded-lg border border-zinc-200 p-5 hover:border-zinc-400 dark:border-zinc-800 dark:hover:border-zinc-600"
        >
          <h2 className="font-semibold mb-1">Items</h2>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            Sample CRUD domain (wired in PR 3).
          </p>
        </Link>
      </div>
    </div>
  );
}

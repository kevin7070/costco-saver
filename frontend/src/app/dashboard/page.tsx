import Link from "next/link";

export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <p className="text-zinc-600 dark:text-zinc-400 mb-6">
        Upload your Costco receipts, review the parsed line items, and keep the
        originals handy for in-store price adjustments.
      </p>
      <div className="grid gap-4 md:grid-cols-2">
        <Link
          href="/dashboard/receipts"
          className="block rounded-lg border border-zinc-200 p-5 hover:border-zinc-400 dark:border-zinc-800 dark:hover:border-zinc-600"
        >
          <h2 className="font-semibold mb-1">Receipts</h2>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            Upload, review, and retrieve your Costco receipts.
          </p>
        </Link>
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

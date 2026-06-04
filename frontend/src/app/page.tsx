import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center">
        <h1 className="text-3xl font-bold mb-4 md:text-4xl">Costco Saver</h1>
        <p className="text-zinc-600 dark:text-zinc-400 mb-8 leading-relaxed">
          Track your Costco purchases and get alerted when something you bought
          drops in price — so you can claim the price difference.
        </p>
        <div className="flex gap-3 justify-center">
          <Link
            href="/login"
            className="rounded-md bg-zinc-900 px-4 py-2 text-white dark:bg-white dark:text-zinc-900"
          >
            Log in
          </Link>
          <Link
            href="/dashboard"
            className="rounded-md border border-zinc-300 px-4 py-2 dark:border-zinc-700"
          >
            Dashboard
          </Link>
        </div>
      </div>
    </main>
  );
}

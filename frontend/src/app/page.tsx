import { Button } from "@/components/ui/catalyst/button";

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
          <Button href="/register">Get started</Button>
          <Button href="/login" outline>
            Log in
          </Button>
        </div>
      </div>
    </main>
  );
}

import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

export const metadata: Metadata = {
  title: "ChatG&T — Martini Loader",
  description: "A line-built martini loading animation.",
};

export default function MartiniLoaderPage() {
  return (
    <main className="min-h-screen bg-steel text-signal">
      <header className="flex min-h-16 items-center justify-between gap-6 border-b border-current px-4 text-xs uppercase sm:px-6">
        <Link className="underline decoration-1 underline-offset-4" href="/martini-studies">
          ← Martini studies
        </Link>
        <span>Loading / Balanced / Loop</span>
      </header>

      <section className="flex min-h-screen items-center justify-center overflow-hidden px-4 py-16 sm:px-6">
        <Image
          alt="A martini glass formed from text, loading one line at a time from bottom to top"
          className="h-auto max-w-full"
          height={640}
          priority
          src="/martini-loader.gif"
          unoptimized
          width={1024}
        />
      </section>
    </main>
  );
}

import type { Metadata } from "next";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "ChatG&T — Learning",
  description: "What the ChatG&T project taught us.",
};

export default function LearningPage() {
  return (
    <main className="min-h-screen bg-concrete text-steel">
      <SiteHeader activePath="/learning" />

      <section className="mx-auto max-w-5xl px-4 pb-20 pt-12 sm:px-6 sm:pb-32 sm:pt-20 lg:max-w-7xl">
        <h1 className="max-w-5xl text-4xl leading-none tracking-tighter sm:text-7xl lg:text-8xl">
          What the work <br /> <span className="text-signal">taught us.</span>
        </h1>
        <div className="mt-8 max-w-2xl text-base leading-relaxed sm:text-lg">
          <p>The experiment produced more than a result.</p>
          <p className="mt-4">This page will bring together the lessons that changed how we think about the work.</p>
        </div>
      </section>

      <aside className="grid border-t border-outline text-xs uppercase sm:grid-cols-2">
        <p className="border-b border-outline px-4 py-6 sm:border-b-0 sm:border-r sm:px-6">Reflection / In progress</p>
        <p className="px-4 py-6 leading-relaxed sm:px-6">What changed / What transfers / What comes next</p>
      </aside>
    </main>
  );
}

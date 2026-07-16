import type { Metadata } from "next";
import { HouseSpecials } from "@/components/house-specials";
import { SiteHeader } from "@/components/site-header";
import { SpiritGuideComposer } from "@/components/spirit-guide-composer";

export const metadata: Metadata = {
  title: "ChatG&T — Tasting Room",
  description: "Try to identify the fine-tuned response.",
};

export default function TastingRoomPage() {
  return (
    <main className="min-h-screen bg-concrete text-steel">
      <SiteHeader activePath="/tasting-room" />

      <section className="mx-auto max-w-5xl px-4 pb-20 pt-12 sm:px-6 sm:pb-32 sm:pt-20 lg:max-w-7xl">
        <h1 className="max-w-5xl text-4xl leading-none tracking-tighter sm:text-7xl lg:text-8xl">
          Can you spot the <br /> <span className="text-signal">fine-tune?</span>
        </h1>
        <div className="mt-8 max-w-2xl text-base leading-relaxed sm:text-lg">
          <p>Two answers. One was prompted with examples. One was fine-tuned.</p>
          <p className="mt-4">Read both, then guess which is which. Your guess is not recorded.</p>
        </div>

        <div className="mt-16 max-w-4xl">
          <SpiritGuideComposer
            actionLabel="Start the tasting"
            label="Choose a tasting"
            placeholder="Ask one question for both samples…"
          />
          <div className="mt-16">
            <HouseSpecials orientation="horizontal" />
          </div>
        </div>
      </section>

      <aside className="grid border-t border-outline text-xs uppercase sm:grid-cols-2">
        <p className="border-b border-outline px-4 py-6 sm:border-b-0 sm:border-r sm:px-6">Blind tasting / 01</p>
        <p className="px-4 py-6 leading-relaxed sm:px-6">Sample A / Sample B / Can&apos;t tell / No guess recorded</p>
      </aside>
    </main>
  );
}

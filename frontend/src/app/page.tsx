import { HouseSpecials } from "@/components/house-specials";
import { SiteHeader } from "@/components/site-header";
import { SpiritGuideComposer } from "@/components/spirit-guide-composer";

export default function SpiritGuidePage() {
  return (
    <main className="min-h-screen bg-concrete text-steel">
      <SiteHeader activePath="/" />

      <section className="mx-auto max-w-5xl px-4 pb-20 pt-12 sm:px-6 sm:pb-32 sm:pt-20 lg:max-w-7xl">
        <h1 className="max-w-5xl text-4xl leading-none tracking-tighter sm:text-7xl lg:text-8xl">
          Useful answers, <br /> <span className="text-signal">mixed differently.</span>
        </h1>
        <div className="mt-8 max-w-2xl text-base leading-relaxed sm:text-lg">
          <p>
            An experiment in teaching a small language model to answer questions as cocktail recipes.
          </p>
          <p className="mt-4">Built for low-stakes questions and fun.</p>
        </div>

        <div className="mt-16 max-w-4xl">
          <SpiritGuideComposer />
          <div className="mt-16">
            <HouseSpecials orientation="horizontal" />
          </div>
        </div>
      </section>

      <aside className="grid border-t border-outline text-xs uppercase sm:grid-cols-2">
        <p className="border-b border-outline px-4 py-6 sm:border-b-0 sm:border-r sm:px-6">Scope / 01</p>
        <p className="px-4 py-6 leading-relaxed sm:px-6">
          English-language / Single-turn / Low-stakes / No live information
        </p>
      </aside>
    </main>
  );
}

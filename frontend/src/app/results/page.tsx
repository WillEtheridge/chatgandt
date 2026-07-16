import type { Metadata } from "next";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "ChatG&T — Results",
  description: "The frozen evidence from the ChatG&T experiment.",
};

const RESULT_AREAS = ["Reliability", "Quality", "Blind preference", "Efficiency"] as const;

export default function ResultsPage() {
  return (
    <main className="min-h-screen bg-concrete text-steel">
      <SiteHeader activePath="/results" />

      <section className="mx-auto max-w-5xl px-4 pb-20 pt-12 sm:px-6 sm:pb-32 sm:pt-20 lg:max-w-7xl">
        <h1 className="max-w-5xl text-4xl leading-none tracking-tighter sm:text-7xl lg:text-8xl">
          Results are <br /> <span className="text-signal">still mixing.</span>
        </h1>
        <div className="mt-8 max-w-2xl text-base leading-relaxed sm:text-lg">
          <p>The controlled evaluation is still in progress.</p>
          <p className="mt-4">This page will publish the frozen evidence when the work is complete.</p>
        </div>

        <div className="mt-16">
          <p className="text-xs uppercase">At a glance / Pending</p>
          <div className="mt-4 grid border-l border-t border-outline sm:grid-cols-2 lg:grid-cols-4">
            {RESULT_AREAS.map((area, index) => (
              <div className="flex min-h-48 flex-col justify-between border-b border-r border-outline p-4 sm:p-6" key={area}>
                <span className="text-xs">0{index + 1} / 04</span>
                <div>
                  <p className="text-lg">{area}</p>
                  <p className="mt-3 text-xs uppercase">Pending final evaluation</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <aside className="grid border-t border-outline text-xs uppercase sm:grid-cols-2">
        <p className="border-b border-outline px-4 py-6 sm:border-b-0 sm:border-r sm:px-6">Evidence / Frozen</p>
        <p className="px-4 py-6 leading-relaxed sm:px-6">No public guesses / No live result updates</p>
      </aside>
    </main>
  );
}

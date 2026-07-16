import type { Metadata } from "next";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "ChatG&T — The Lab",
  description: "Understand the ChatG&T experiment and its method.",
};

const LAB_SECTIONS = [
  "Research question",
  "Four systems",
  "Successful pour",
  "Training process",
  "Fair test",
  "Measurements",
  "Boundaries",
  "Next destinations",
] as const;

export default function LabPage() {
  return (
    <main className="min-h-screen bg-concrete text-steel">
      <SiteHeader activePath="/lab" />

      <section className="mx-auto max-w-5xl px-4 pb-20 pt-12 sm:px-6 sm:pb-32 sm:pt-20 lg:max-w-7xl">
        <h1 className="max-w-5xl text-4xl leading-none tracking-tighter sm:text-7xl lg:text-8xl">
          Inside the <br /> <span className="text-signal">experiment.</span>
        </h1>
        <div className="mt-8 max-w-2xl text-base leading-relaxed sm:text-lg">
          <p>How do prompting and fine-tuning change the reliability, quality, and cost of a small language model?</p>
          <p className="mt-4">The Lab explains the method. Results explains what happened.</p>
        </div>

        <div className="mt-16">
          <p className="text-xs uppercase">Method / Contents</p>
          <ol className="mt-4 grid border-l border-t border-outline sm:grid-cols-2 lg:grid-cols-4">
            {LAB_SECTIONS.map((section, index) => (
              <li className="flex min-h-48 flex-col justify-between border-b border-r border-outline p-4 sm:p-6" key={section}>
                <span className="text-xs">{String(index + 1).padStart(2, "0")}</span>
                <span className="text-lg">{section}</span>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <aside className="grid border-t border-outline text-xs uppercase sm:grid-cols-2">
        <p className="border-b border-outline px-4 py-6 sm:border-b-0 sm:border-r sm:px-6">Method / Not outcome</p>
        <p className="px-4 py-6 leading-relaxed sm:px-6">Frozen systems / Unseen prompts / Blind evaluation</p>
      </aside>
    </main>
  );
}

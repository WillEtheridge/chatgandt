import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "ChatG&T — Typography",
  description: "Neue Montreal Mono and colour workbench.",
};

export default function TypeColourWorkbench() {
  return (
    <main>
      <header className="flex min-h-16 items-center justify-between gap-6 border-b border-current px-4 text-xs uppercase sm:px-6">
        <Link className="underline decoration-1 underline-offset-4" href="/">
          ChatG&amp;T
        </Link>
        <Link className="text-right underline decoration-1 underline-offset-4" href="/martini-studies">
          Martini studies →
        </Link>
      </header>

      <section className="grid min-h-80 sm:grid-cols-3">
        <div className="flex flex-col justify-between border-b border-current bg-concrete p-4 text-steel sm:min-h-96 sm:border-r sm:p-6">
          <p className="text-xs uppercase">Background / 01</p>
          <div>
            <p className="text-5xl leading-none tracking-tight lg:text-7xl">F0EEE9</p>
            <p className="mt-3 text-xs uppercase">Warm concrete</p>
          </div>
        </div>
        <div className="flex flex-col justify-between border-b border-current bg-steel p-4 text-concrete sm:min-h-96 sm:border-r sm:p-6">
          <p className="text-xs uppercase">Type / 02</p>
          <div>
            <p className="text-5xl leading-none tracking-tight lg:text-7xl">020D13</p>
            <p className="mt-3 text-xs uppercase">Deep steel</p>
          </div>
        </div>
        <div className="flex flex-col justify-between border-b border-current bg-signal p-4 text-steel sm:min-h-96 sm:p-6">
          <p className="text-xs uppercase">Signal / 03</p>
          <div>
            <p className="text-5xl leading-none tracking-tight lg:text-7xl">CD533B</p>
            <p className="mt-3 text-xs uppercase">Oxide red</p>
          </div>
        </div>
      </section>

      <section>
        <div className="border-b border-current px-4 py-6 sm:px-6">
          <p className="text-xs uppercase">Typography scale / Proposal 01 / Book 400</p>
        </div>

        <div className="border-b border-current px-4 py-14 sm:px-6 sm:py-20">
          <p className="mb-10 text-xs uppercase text-signal">H1 / Book 400</p>
          <h1 className="max-w-6xl text-6xl leading-none tracking-tighter sm:text-8xl lg:text-9xl">
            Experimental mixology.
          </h1>
        </div>

        <div className="border-b border-current px-4 py-14 sm:px-6 sm:py-20">
          <p className="mb-10 text-xs uppercase text-signal">H2 / Book 400</p>
          <h2 className="max-w-5xl text-5xl leading-none tracking-tighter sm:text-7xl lg:text-8xl">
            Useful answers, mixed differently.
          </h2>
        </div>

        <div className="border-b border-current px-4 py-14 sm:px-6 sm:py-20">
          <p className="mb-10 text-xs uppercase text-signal">H3 / Book 400</p>
          <h3 className="max-w-4xl text-4xl leading-tight tracking-tight sm:text-5xl lg:text-6xl">
            Prompt engineering or fine-tuning?
          </h3>
        </div>

        <div className="border-b border-current px-4 py-12 sm:px-6 sm:py-16">
          <p className="mb-10 text-xs uppercase text-signal">H4 / Book 400</p>
          <h4 className="max-w-3xl text-2xl leading-tight tracking-tight sm:text-3xl lg:text-4xl">
            Ingredients / Method / Garnish
          </h4>
        </div>

        <div className="border-b border-current px-4 py-12 sm:px-6 sm:py-16">
          <p className="mb-10 text-xs uppercase text-signal">Body / Book 400</p>
          <p className="max-w-3xl text-base leading-relaxed sm:text-lg">
            ChatG&amp;T is an experiment in teaching a small language model to answer useful questions as metaphorical cocktail recipes. The recipe is not decoration around the answer; it is the structure through which the answer is understood.
          </p>
        </div>
      </section>

      <section className="px-4 py-16 sm:px-6 sm:py-24">
        <p className="mb-10 text-xs uppercase">Mixing language / Book 400</p>
        <div className="space-y-2 text-4xl leading-none tracking-tighter sm:text-6xl lg:text-8xl">
          <p>POUR_01</p>
          <p>{"////////////////"}</p>
          <p>MIXING</p>
          <p className="tracking-tighter">■■■■■■□□□□</p>
        </div>
      </section>

      <section className="border-t border-current px-4 py-16 sm:px-6 sm:py-24">
        <p className="mb-10 text-xs uppercase">Glyphs / Numerals / Punctuation / Book 400</p>
        <p className="max-w-5xl break-all text-4xl leading-tight tracking-tight sm:text-6xl lg:text-7xl">
          {"ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789 {}[]() <> /\\ +−×÷ =!? @#$%& →↗↘← ■□"}
        </p>
      </section>

    </main>
  );
}

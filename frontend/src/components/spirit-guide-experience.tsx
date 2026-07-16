"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import { HouseSpecials } from "@/components/house-specials";
import { Recipe, type ChatGntRecipe } from "@/components/recipe";
import { SpiritGuideComposer } from "@/components/spirit-guide-composer";

const MOCK_RECIPE: ChatGntRecipe = {
  garnish: "One clear worktop as visible proof of progress.",
  ingredients: [
    { amount: 50, name: "functional impact", unit: "ml" },
    { amount: 25, name: "visible progress", unit: "ml" },
    { amount: 15, name: "uninterrupted focus", unit: "minutes" },
    { amount: 2, name: "hazard awareness", unit: "dashes" },
    { amount: 1, name: "basket for anything belonging elsewhere", unit: "measure" },
  ],
  method: [
    "Skim off anything urgent—spills, spoiled food, or blocked walkways—before choosing the main pour.",
    "Stir functional impact together with visible progress, then choose the chore that will restore the most useful space within fifteen minutes.",
    "Pour your full attention into that one task, straining anything that belongs elsewhere into the basket instead of leaving the room.",
    "Serve the finished win, then decide whether to stop or mix a second round.",
  ],
  title: "The Clear-Surface Collins",
};

type Phase = "editing" | "idle" | "mixing" | "recipe";

export function SpiritGuideExperience() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [order, setOrder] = useState("");
  const isActive = phase !== "idle";

  useEffect(() => {
    if (phase !== "mixing") return;
    const finishedMixing = window.setTimeout(() => setPhase("recipe"), 2400);
    return () => window.clearTimeout(finishedMixing);
  }, [phase]);

  function mixOrder(submittedOrder: string) {
    setOrder(submittedOrder);
    setPhase("mixing");
    window.scrollTo(0, 0);
  }

  function mixAnother() {
    setOrder("");
    setPhase("idle");
    window.scrollTo(0, 0);
  }

  if (!isActive) {
    return (
      <>
        <section className="mx-auto max-w-5xl px-4 pb-20 pt-12 sm:px-6 sm:pb-32 sm:pt-20 lg:max-w-7xl">
          <h1 className="max-w-5xl text-4xl leading-none tracking-tighter sm:text-7xl lg:text-8xl">
            Useful answers, <br /> <span className="text-signal">mixed differently.</span>
          </h1>
          <div className="mt-8 max-w-2xl text-base leading-relaxed sm:text-lg">
            <p>An experiment in teaching a small language model to answer questions as cocktail recipes.</p>
            <p className="mt-4">Built for low-stakes questions and fun.</p>
          </div>

          <div className="mt-16 max-w-4xl">
            <SpiritGuideComposer onSubmit={mixOrder} onValueChange={setOrder} value={order} />
            <div className="mt-16">
              <HouseSpecials onSelect={setOrder} orientation="horizontal" />
            </div>
          </div>
        </section>

        <aside className="grid border-t border-outline text-xs uppercase sm:grid-cols-2">
          <p className="border-b border-outline px-4 py-6 sm:border-b-0 sm:border-r sm:px-6">Scope / 01</p>
          <p className="px-4 py-6 leading-relaxed sm:px-6">
            English-language / Single-turn / Low-stakes / No live information
          </p>
        </aside>
      </>
    );
  }

  return (
    <>
      <section className="mx-auto min-h-screen max-w-5xl px-4 pb-64 pt-4 sm:px-6 sm:pt-8 lg:max-w-7xl">
        <div className="grid gap-12 lg:grid-cols-4 lg:gap-8">
          <aside className="lg:col-span-1">
            <p className="text-xs uppercase text-signal">Order_01</p>
            <p className="mt-4 text-xl leading-relaxed sm:text-2xl">{order}</p>
          </aside>

          <div className="lg:col-span-3">
            {phase === "mixing" ? (
            <div className="border-t border-outline pt-8" aria-live="polite">
              <p className="text-xs uppercase">Mixing your answer…</p>
              <Image
                alt="Text forming a martini glass line by line"
                className="mt-8 h-auto w-full max-w-3xl motion-reduce:hidden"
                height={640}
                priority
                src="/martini-loader.gif"
                unoptimized
                width={1024}
              />
              <p className="mt-8 hidden text-lg motion-reduce:block">Your answer is being mixed.</p>
            </div>
            ) : (
            <div>
              <Recipe recipe={MOCK_RECIPE} />
            </div>
            )}
          </div>
        </div>
      </section>

      <div className="fixed bottom-0 left-0 right-0 z-10 border-t border-outline bg-concrete">
        <div className="mx-auto w-full max-w-5xl px-4 py-4 sm:px-6 lg:max-w-7xl">
          <div className="max-w-4xl">
            <SpiritGuideComposer
              disabled={phase !== "editing"}
              hideLabel
              onSubmit={mixOrder}
              onValueChange={setOrder}
              value={order}
            />
          </div>
        </div>
      </div>
    </>
  );
}

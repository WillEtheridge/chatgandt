"use client";

import { useState } from "react";
import { getRandomHouseSpecial } from "@/components/house-specials";
import { MartiniLoader } from "@/components/martini-loader";
import { FailureResult, type ModelOutcome } from "@/components/model-outcome";
import { Recipe } from "@/components/recipe";
import { SpiritGuideComposer } from "@/components/spirit-guide-composer";
import { requestSpiritGuide } from "@/lib/chatgnt-api-client";

type Phase = "idle" | "mixing" | "recipe";

export function SpiritGuideExperience() {
  const [outcome, setOutcome] = useState<ModelOutcome | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [order, setOrder] = useState("");
  const [submittedOrder, setSubmittedOrder] = useState("");
  const isActive = phase !== "idle";

  async function mixOrder(submittedValue: string) {
    setOrder(submittedValue);
    setSubmittedOrder(submittedValue);
    setOutcome(null);
    setPhase("mixing");
    window.scrollTo(0, 0);
    try {
      setOutcome((await requestSpiritGuide(submittedValue)).outcome);
    } catch {
      setOutcome({ status: "failure", failure: "operational" });
    } finally {
      setPhase("recipe");
    }
  }

  if (!isActive) {
    return (
      <>
        <section className="mx-auto max-w-5xl px-4 pb-64 pt-12 sm:px-6 sm:pt-20 lg:max-w-7xl">
          <h1 className="max-w-5xl text-4xl leading-none tracking-tighter sm:text-7xl lg:text-8xl">
            Useful answers, <br /> <span className="text-signal">mixed differently.</span>
          </h1>
          <div className="mt-8 max-w-2xl text-base leading-relaxed sm:text-lg">
            <p>An experiment in teaching a small language model to answer questions as cocktail recipes.</p>
            <p className="mt-4">Built for low-stakes questions and fun.</p>
          </div>
        </section>

        <div className="fixed bottom-0 left-0 right-0 z-10 border-t border-outline bg-concrete">
          <div className="mx-auto w-full max-w-5xl px-4 py-4 sm:px-6 lg:max-w-7xl">
            <div className="flex flex-col gap-2 sm:flex-row">
              <div className="min-w-0 flex-1">
                <SpiritGuideComposer
                  hideLabel
                  onSubmit={mixOrder}
                  onValueChange={setOrder}
                  value={order}
                />
              </div>
              <button
                className="min-h-14 w-full shrink-0 cursor-pointer whitespace-nowrap border border-signal px-4 py-3 text-left text-xs uppercase hover:bg-steel hover:text-concrete sm:w-fit"
                onClick={() => mixOrder(getRandomHouseSpecial())}
                type="button"
              >
                Bartender&apos;s Choice
              </button>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <section className="mx-auto min-h-screen max-w-5xl px-4 pb-64 pt-4 sm:px-6 sm:pt-8 lg:max-w-7xl">
        <div className="grid gap-12 lg:grid-cols-4 lg:gap-8">
          <aside className="lg:col-span-1">
            <p className="text-xs uppercase text-signal">Order_01</p>
            <p className="mt-4 text-xl leading-relaxed sm:text-2xl">{submittedOrder}</p>
          </aside>

          <div className="lg:col-span-3">
            {phase === "mixing" ? (
            <div aria-live="polite">
              <MartiniLoader />
            </div>
            ) : (
            <div>
              {outcome?.status === "valid" ? <Recipe recipe={outcome.recipe} /> : <FailureResult failure={outcome?.failure ?? "operational"} />}
            </div>
            )}
          </div>
        </div>
      </section>

      <div className="fixed bottom-0 left-0 right-0 z-10 border-t border-outline bg-concrete">
        <div className="mx-auto w-full max-w-5xl px-4 py-4 sm:px-6 lg:max-w-7xl">
          <div className="flex flex-col gap-2 sm:flex-row">
            <div className="min-w-0 flex-1">
            <SpiritGuideComposer
              disabled={phase === "mixing"}
              hideLabel
              onSubmit={mixOrder}
              onValueChange={setOrder}
              value={order}
            />
            </div>
            <button
              className="min-h-14 w-full shrink-0 cursor-pointer whitespace-nowrap border border-signal px-4 py-3 text-left text-xs uppercase hover:bg-steel hover:text-concrete disabled:cursor-wait sm:w-fit"
              disabled={phase === "mixing"}
              onClick={() => mixOrder(getRandomHouseSpecial())}
              type="button"
            >
              Bartender&apos;s Choice
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

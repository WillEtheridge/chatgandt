"use client";

import { useEffect, useState } from "react";
import { getRandomHouseSpecial } from "@/components/house-specials";
import { MartiniLoader } from "@/components/martini-loader";
import { Recipe, type ChatGntRecipe } from "@/components/recipe";
import { SpiritGuideComposer } from "@/components/spirit-guide-composer";

const RECIPES: Record<AnswerNumber, ChatGntRecipe> = {
  1: {
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
  },
  2: {
    garnish: "A cleared patch of room and permission to stop after one useful win.",
    ingredients: [
      { amount: 45, name: "most useful room", unit: "ml" },
      { amount: 30, name: "quick visible win", unit: "ml" },
      { amount: 15, name: "focused effort", unit: "minutes" },
      { amount: 1, name: "temporary clutter basket", unit: "measure" },
    ],
    method: [
      "Choose the room whose mess is getting in the way of daily life most often.",
      "Pick one task that creates a visible result in fifteen minutes: clear a worktop, wash the dishes, or gather loose laundry.",
      "Put anything that belongs elsewhere into one basket so you can finish without wandering between rooms.",
      "Stop when the timer ends, notice the improvement, and only continue if you genuinely have the energy.",
    ],
    title: "The First-Win Highball",
  },
};

type AnswerNumber = 1 | 2;
type Phase = "idle" | "mixing" | "tasting" | "revealed";

export function TastingRoomExperience() {
  const [activeAnswer, setActiveAnswer] = useState<AnswerNumber>(1);
  const [draft, setDraft] = useState("");
  const [fineTunedAnswer, setFineTunedAnswer] = useState<AnswerNumber>(1);
  const [phase, setPhase] = useState<Phase>("idle");
  const [preference, setPreference] = useState<AnswerNumber | null>(null);
  const [submittedOrder, setSubmittedOrder] = useState("");
  const isActive = phase !== "idle";

  useEffect(() => {
    if (phase !== "mixing") return;
    const finishedMixing = window.setTimeout(() => setPhase("tasting"), 2400);
    return () => window.clearTimeout(finishedMixing);
  }, [phase]);

  function startTasting(submittedValue: string) {
    setDraft(submittedValue);
    setSubmittedOrder(submittedValue);
    setActiveAnswer(1);
    setFineTunedAnswer(Math.random() < 0.5 ? 1 : 2);
    setPreference(null);
    setPhase("mixing");
    window.scrollTo(0, 0);
  }

  function chooseAnswer() {
    setPreference(activeAnswer);
    setPhase("revealed");
  }

  const composer = (
    <div className={`fixed bottom-0 left-0 right-0 z-10 bg-concrete ${isActive ? "border-t border-outline" : ""}`}>
      <div className="mx-auto w-full max-w-5xl px-4 py-4 sm:px-6 lg:max-w-7xl">
        <div className="flex flex-col gap-2 sm:flex-row">
          <div className="min-w-0 flex-1">
            <SpiritGuideComposer
              actionLabel="Start the tasting"
              disabled={phase === "mixing"}
              hideLabel
              onSubmit={startTasting}
              onValueChange={setDraft}
              placeholder="Ask one question for both samples…"
              value={draft}
            />
          </div>
          <button
            className="min-h-14 w-full shrink-0 cursor-pointer whitespace-nowrap border border-signal px-4 py-3 text-left text-xs uppercase hover:bg-steel hover:text-concrete disabled:cursor-wait sm:w-fit"
            disabled={phase === "mixing"}
            onClick={() => startTasting(getRandomHouseSpecial())}
            type="button"
          >
            Bartender&apos;s Choice
          </button>
        </div>
      </div>
    </div>
  );

  if (!isActive) {
    return (
      <>
        <section className="mx-auto max-w-5xl px-4 pb-64 pt-12 sm:px-6 sm:pt-20 lg:max-w-7xl">
          <h1 className="max-w-5xl text-4xl leading-none tracking-tighter sm:text-7xl lg:text-8xl">
            Can you spot the <br /> <span className="text-signal">fine-tune?</span>
          </h1>
          <div className="mt-8 max-w-2xl text-base leading-relaxed sm:text-lg">
            <p>Two answers. One was prompted with examples. One was fine-tuned.</p>
            <p className="mt-4">Read both, choose the one you prefer, then see which was which.</p>
          </div>
        </section>
        {composer}
      </>
    );
  }

  return (
    <>
      <section className="mx-auto min-h-screen max-w-5xl px-4 pb-64 pt-4 sm:px-6 sm:pt-8 lg:max-w-7xl">
        <div className="grid gap-12 lg:grid-cols-4 lg:gap-8">
          <aside className="lg:col-span-1">
            <p className="text-xs uppercase text-signal">Tasting_01</p>
            <p className="mt-4 text-xl leading-relaxed sm:text-2xl">{submittedOrder}</p>
          </aside>

          <div className="lg:col-span-3">
            {phase === "mixing" ? (
              <div aria-live="polite">
                <MartiniLoader />
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 border border-outline">
                  {([1, 2] as const).map((answer) => (
                    <button
                      aria-pressed={activeAnswer === answer}
                      className={`cursor-pointer px-4 py-4 text-left text-xs uppercase first:border-r first:border-outline ${
                        activeAnswer === answer ? "bg-steel text-concrete" : "hover:text-signal"
                      }`}
                      key={answer}
                      onClick={() => setActiveAnswer(answer)}
                      type="button"
                    >
                      Answer {String(answer).padStart(2, "0")}
                    </button>
                  ))}
                </div>

                <div className="mt-2">
                  <Recipe recipe={RECIPES[activeAnswer]} />
                </div>

                {phase === "tasting" ? (
                  <button
                    className="mt-2 w-full cursor-pointer border border-signal px-4 py-4 text-left text-xs uppercase hover:bg-signal hover:text-concrete"
                    onClick={chooseAnswer}
                    type="button"
                  >
                    Choose answer {String(activeAnswer).padStart(2, "0")}
                  </button>
                ) : (
                  <div className="mt-2 grid border border-outline sm:grid-cols-2" aria-live="polite">
                    {([1, 2] as const).map((answer) => (
                      <p
                        className={`px-4 py-4 text-xs uppercase first:border-b first:border-outline sm:first:border-b-0 sm:first:border-r ${
                          preference === answer ? "text-signal" : ""
                        }`}
                        key={answer}
                      >
                        Answer {String(answer).padStart(2, "0")} / {fineTunedAnswer === answer ? "Fine-tuned" : "Prompted"}
                        {preference === answer ? " / Your choice" : ""}
                      </p>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </section>
      {composer}
    </>
  );
}

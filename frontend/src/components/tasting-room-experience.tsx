"use client";

import { useState } from "react";
import { getRandomHouseSpecial } from "@/components/house-specials";
import { MartiniLoader } from "@/components/martini-loader";
import { FailureResult, type ModelOutcome } from "@/components/model-outcome";
import { Recipe } from "@/components/recipe";
import { SpiritGuideComposer } from "@/components/spirit-guide-composer";
import { requestTastingRoom } from "@/lib/chatgnt-api-client";

type AnswerNumber = 1 | 2;
type Phase = "idle" | "mixing" | "tasting" | "revealed";
type Preference = AnswerNumber | "neither" | null;

function validOutcomes(): Record<AnswerNumber, ModelOutcome> {
  return {
    1: { status: "failure", failure: "operational" },
    2: { status: "failure", failure: "operational" },
  };
}

export function TastingRoomExperience() {
  const [activeAnswer, setActiveAnswer] = useState<AnswerNumber>(1);
  const [draft, setDraft] = useState("");
  const [fineTunedAnswer, setFineTunedAnswer] = useState<AnswerNumber>(1);
  const [outcomes, setOutcomes] = useState<Record<AnswerNumber, ModelOutcome>>(validOutcomes);
  const [phase, setPhase] = useState<Phase>("idle");
  const [preference, setPreference] = useState<Preference>(null);
  const [submittedOrder, setSubmittedOrder] = useState("");
  const isActive = phase !== "idle";

  async function startTasting(submittedValue: string) {
    setDraft(submittedValue);
    setSubmittedOrder(submittedValue);
    setActiveAnswer(1);
    setOutcomes(validOutcomes());
    setPreference(null);
    setPhase("mixing");
    window.scrollTo(0, 0);
    try {
      const tasting = await requestTastingRoom(submittedValue);
      setFineTunedAnswer(tasting.fineTunedAnswer);
      setOutcomes(tasting.answers);
    } catch {
      setOutcomes(validOutcomes());
    } finally {
      setPhase("tasting");
    }
  }

  function chooseAnswer() {
    setPreference(activeAnswer);
    setPhase("revealed");
  }

  const bothAnswersFailed = outcomes[1].status === "failure" && outcomes[2].status === "failure";

  const composer = (
    <div className="fixed bottom-0 left-0 right-0 z-10 border-t border-outline bg-concrete">
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
                  {outcomes[activeAnswer].status === "valid" ? (
                    <Recipe recipe={outcomes[activeAnswer].recipe} />
                  ) : (
                    <FailureResult failure={outcomes[activeAnswer].failure} />
                  )}
                </div>

                {phase === "tasting" ? (
                  <div className={`mt-2 grid ${bothAnswersFailed ? "sm:grid-cols-2" : ""}`}>
                    <button
                      className="w-full cursor-pointer border border-signal px-4 py-4 text-left text-xs uppercase hover:bg-signal hover:text-concrete"
                      onClick={chooseAnswer}
                      type="button"
                    >
                      Choose answer {String(activeAnswer).padStart(2, "0")}
                    </button>
                    {bothAnswersFailed && (
                      <button
                        className="w-full cursor-pointer border border-signal px-4 py-4 text-left text-xs uppercase hover:bg-signal hover:text-concrete sm:border-l-0"
                        onClick={() => {
                          setPreference("neither");
                          setPhase("revealed");
                        }}
                        type="button"
                      >
                        Choose neither
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="mt-2 border border-outline" aria-live="polite">
                    <div className="grid sm:grid-cols-2">
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
                    {preference === "neither" && (
                      <p className="border-t border-outline px-4 py-4 text-xs uppercase text-signal">Neither / Your choice</p>
                    )}
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

"use client";

import { useEffect, useState } from "react";

const HOUSE_SPECIALS = [
  "Help me prepare for a difficult conversation.",
  "Explain compound interest in plain English.",
  "Plan a focused afternoon of work.",
  "Help me say no without sounding rude.",
  "Explain what an API does using a simple analogy.",
  "Plan a relaxed dinner party for six people.",
  "Break an intimidating task into manageable steps.",
  "Help me prepare for a job interview.",
  "Turn a loose discussion into a useful meeting agenda.",
  "Brainstorm thoughtful birthday gifts for a close friend.",
  "Help me build a realistic daily reading habit.",
  "Explain confirmation bias with an everyday example.",
  "Write a friendly follow-up email after a meeting.",
  "Help me organise a cluttered workspace.",
  "Suggest useful questions to ask a new mentor.",
  "Help me resolve a scheduling conflict politely.",
  "Explain recursion without using technical jargon.",
  "Outline a short story about an unexpected visitor.",
  "Create a simple weekly meal-planning routine.",
  "Help me give constructive feedback to a colleague.",
  "Suggest a new hobby I could try at home.",
  "Rewrite a technical paragraph for a general audience.",
  "Plan a fun afternoon indoors on a rainy day.",
  "Explain the greenhouse effect in simple terms.",
  "Turn a page of notes into a clear presentation outline.",
  "Make a one-week study plan for a difficult subject.",
  "Help me welcome a new teammate.",
  "Brainstorm names for a small creative project.",
  "Help me weigh the pros and cons of two options.",
  "Explain why the sky changes colour at sunset.",
] as const;

function chooseSpecials(items: readonly string[]) {
  const shuffled = [...items];

  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const randomIndex = Math.floor(Math.random() * (index + 1));
    [shuffled[index], shuffled[randomIndex]] = [shuffled[randomIndex], shuffled[index]];
  }

  return shuffled.slice(0, 3);
}

export function HouseSpecials({
  items = HOUSE_SPECIALS,
  orientation = "stacked",
}: Readonly<{ items?: readonly string[]; orientation?: "horizontal" | "stacked" }>) {
  const isHorizontal = orientation === "horizontal";
  const [visibleItems, setVisibleItems] = useState(() => items.slice(0, 3));

  useEffect(() => {
    const selection = window.setTimeout(() => setVisibleItems(chooseSpecials(items)), 0);
    return () => window.clearTimeout(selection);
  }, [items]);

  return (
    <div>
      <p className="text-xs uppercase">House Specials</p>
      <div
        className={
          isHorizontal
            ? "mt-4 grid border border-outline sm:grid-cols-3"
            : "mt-4 grid h-72 grid-rows-3 border border-outline"
        }
      >
        {visibleItems.map((item) => (
          <button
            className={
              isHorizontal
                ? "flex min-h-32 w-full cursor-pointer items-start justify-between gap-6 border-b border-outline px-4 py-4 text-left text-sm leading-relaxed last:border-b-0 hover:bg-steel hover:text-concrete sm:border-b-0 sm:border-r sm:px-6 sm:last:border-r-0"
                : "flex h-full w-full cursor-pointer items-start justify-between gap-6 border-b border-outline px-4 py-4 text-left text-sm leading-relaxed last:border-b-0 hover:bg-steel hover:text-concrete sm:px-6"
            }
            key={item}
            type="button"
          >
            <span>{item}</span>
            <span aria-hidden="true">↗</span>
          </button>
        ))}
      </div>
    </div>
  );
}

"use client";

import type { FormEvent } from "react";
import { LiaCocktailSolid } from "react-icons/lia";

export function SpiritGuideComposer({
  actionLabel = "Mix it",
  label = "Place your order",
  placeholder = "Ask a low-stakes question…",
}: Readonly<{ actionLabel?: string; label?: string; placeholder?: string }>) {
  function resizeOrder(event: FormEvent<HTMLTextAreaElement>) {
    const order = event.currentTarget;
    order.style.height = "auto";
    order.style.height = `${order.scrollHeight}px`;
  }

  return (
    <form onSubmit={(event) => event.preventDefault()}>
      <label className="block text-xs uppercase" htmlFor="order">
        {label}
      </label>
      <div className="mt-4 flex items-end border border-outline pl-2">
        <textarea
          className="max-h-48 min-h-10 flex-1 self-center resize-none overflow-y-auto bg-transparent px-2 py-2 text-base leading-relaxed outline-none placeholder:text-steel sm:text-lg"
          id="order"
          name="order"
          onInput={resizeOrder}
          placeholder={placeholder}
          required
          rows={1}
        />
        <button
          aria-label={actionLabel}
          className="my-2 ml-1 mr-2 flex size-10 shrink-0 cursor-pointer items-center justify-center bg-signal text-concrete"
          title={actionLabel}
          type="submit"
        >
          <LiaCocktailSolid aria-hidden="true" className="text-2xl" />
          <span className="sr-only">{actionLabel}</span>
        </button>
      </div>
    </form>
  );
}

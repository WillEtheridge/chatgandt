"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useRef, useState } from "react";
import { LiaCocktailSolid } from "react-icons/lia";
import { MAX_PROMPT_CHARACTERS } from "@/lib/chatgnt-contract";

export function SpiritGuideComposer({
  actionLabel = "Mix it",
  disabled = false,
  hideLabel = false,
  label = "Place your order",
  onSubmit,
  onValueChange,
  placeholder = "Ask a low-stakes question…",
  value,
}: Readonly<{
  actionLabel?: string;
  disabled?: boolean;
  hideLabel?: boolean;
  label?: string;
  onSubmit?: (value: string) => void;
  onValueChange?: (value: string) => void;
  placeholder?: string;
  value?: string;
}>) {
  const [internalValue, setInternalValue] = useState("");
  const orderRef = useRef<HTMLTextAreaElement>(null);
  const orderValue = value ?? internalValue;

  useEffect(() => {
    const order = orderRef.current;
    if (!order) return;
    order.style.height = "auto";
    order.style.height = `${order.scrollHeight}px`;
  }, [orderValue]);

  function resizeOrder(event: FormEvent<HTMLTextAreaElement>) {
    const order = event.currentTarget;
    order.style.height = "auto";
    order.style.height = `${order.scrollHeight}px`;
  }

  function updateOrder(event: ChangeEvent<HTMLTextAreaElement>) {
    const nextValue = event.currentTarget.value;
    setInternalValue(nextValue);
    onValueChange?.(nextValue);
  }

  function submitOrder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const submittedValue = orderValue.trim();
    if (submittedValue) onSubmit?.(submittedValue);
  }

  return (
    <form onSubmit={submitOrder}>
      {!hideLabel && (
        <label className="block text-xs uppercase" htmlFor="order">
          {label}
        </label>
      )}
      <div className={`${hideLabel ? "" : "mt-4"} flex items-end border border-outline pl-2`}>
        <textarea
          className="max-h-48 min-h-10 flex-1 self-center resize-none overflow-y-auto bg-transparent px-2 py-2 text-base leading-relaxed outline-none placeholder:text-steel sm:text-lg"
          id="order"
          maxLength={MAX_PROMPT_CHARACTERS}
          name="order"
          onChange={updateOrder}
          onInput={resizeOrder}
          placeholder={placeholder}
          readOnly={disabled}
          ref={orderRef}
          required
          rows={1}
          value={orderValue}
        />
        <button
          aria-label={actionLabel}
          className="my-2 ml-1 mr-2 flex size-10 shrink-0 cursor-pointer items-center justify-center bg-signal text-concrete disabled:cursor-wait"
          disabled={disabled}
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

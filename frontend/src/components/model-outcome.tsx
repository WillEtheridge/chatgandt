import type { FailureKind } from "@/lib/chatgnt-contract";

export type { FailureKind, ModelOutcome } from "@/lib/chatgnt-contract";

const FAILURE_COPY: Record<FailureKind, { title: string; detail: string }> = {
  "invalid-json": {
    title: "Invalid JSON",
    detail: "This model completed its response, but did not return valid JSON.",
  },
  "invalid-schema": {
    title: "Invalid recipe structure",
    detail: "This model returned JSON, but it did not match the required ChatG&T cocktail-recipe structure.",
  },
  operational: {
    title: "The bar is backed up",
    detail: "This order could not be completed because the model service failed. Please try again.",
  },
};

export function FailureResult({ failure }: Readonly<{ failure: FailureKind }>) {
  const copy = FAILURE_COPY[failure];

  return (
    <section className="border border-outline" aria-live="polite">
      <div className="border-b border-outline p-4 sm:p-6">
        <p className="text-xs uppercase text-signal">Generation failure</p>
        <h2 className="mt-6 text-3xl leading-none tracking-tighter sm:text-4xl">{copy.title}</h2>
      </div>
      <p className="max-w-3xl p-4 text-sm leading-relaxed sm:p-6">{copy.detail}</p>
    </section>
  );
}

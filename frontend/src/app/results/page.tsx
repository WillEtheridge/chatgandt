import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "ChatG&T — Results",
  description:
    "Fine-tuning improved ChatG&T's structural reliability and prompt efficiency, but not clearly its answer quality.",
};

const QUALITY_RESULTS = [
  {
    label: "Underlying answer",
    prompted: "19 / 60",
    tuned: "29 / 60",
    note: "Was the advice itself useful and correct?",
  },
  {
    label: "Cocktail metaphor",
    prompted: "33 / 60",
    tuned: "42 / 60",
    note: "Did the drink meaningfully express the advice?",
  },
  {
    label: "Recipe execution",
    prompted: "39 / 60",
    tuned: "45 / 60",
    note: "Did it read like a plausible cocktail recipe?",
  },
] as const;

function Section({
  children,
  number,
  title,
}: Readonly<{ children: ReactNode; number: string; title: string }>) {
  const id = `result-${number}`;

  return (
    <section aria-labelledby={id} className="border-t border-outline py-16 sm:py-24">
      <div className="grid gap-10 lg:grid-cols-4 lg:gap-16">
        <header>
          <p className="text-xs uppercase text-signal">{number}</p>
          <h2 className="mt-4 text-3xl leading-tight tracking-tighter sm:text-4xl" id={id}>
            {title}
          </h2>
        </header>
        <div className="lg:col-span-3">{children}</div>
      </div>
    </section>
  );
}

function Prose({ children, className = "" }: Readonly<{ children: ReactNode; className?: string }>) {
  return <div className={`max-w-3xl space-y-5 text-base leading-relaxed ${className}`}>{children}</div>;
}

function ResultFigure({
  label,
  note,
  value,
}: Readonly<{ label: string; note: string; value: string }>) {
  return (
    <div className="flex min-h-56 flex-col justify-between border-b border-r border-outline p-5 sm:p-6">
      <p className="text-xs uppercase">{label}</p>
      <div>
        <p className="text-4xl leading-none tracking-tighter text-signal sm:text-5xl">{value}</p>
        <p className="mt-4 max-w-xs text-sm leading-relaxed">{note}</p>
      </div>
    </div>
  );
}

export default function ResultsPage() {
  return (
    <main className="min-h-screen bg-concrete text-steel">
      <SiteHeader activePath="/results" />

      <article className="mx-auto max-w-5xl px-4 pb-20 pt-12 sm:px-6 sm:pb-32 sm:pt-20 lg:max-w-7xl">
        <header className="pb-16 sm:pb-24">
          <p className="text-xs uppercase text-signal">Results / Frozen held-out evaluation</p>
          <h1 className="mt-6 max-w-6xl text-4xl leading-none tracking-tighter sm:text-6xl lg:text-7xl">
            Fine-tuning improved the structure. <span className="text-signal">Answer quality remained uncertain.</span>
          </h1>

          <div className="mt-16 grid gap-6 border-t border-outline pt-6 lg:grid-cols-4 lg:gap-12">
            <p className="text-xs uppercase">The research question</p>
            <p className="max-w-4xl text-xl leading-relaxed sm:text-2xl lg:col-span-3">
              How does LoRA-based supervised fine-tuning compare with a strong five-shot prompt in producing
              schema-valid, useful, metaphorically coherent, and stylistically consistent ChatG&T responses on unseen
              prompts—and what trade-offs does it introduce in prompt-token usage and latency?
            </p>
          </div>
        </header>

        <section aria-labelledby="short-answer" className="bg-steel px-5 py-12 text-concrete sm:px-10 sm:py-16">
          <div className="grid gap-8 lg:grid-cols-4 lg:gap-16">
            <p className="text-xs uppercase text-signal" id="short-answer">
              TLDR
            </p>
            <div className="max-w-4xl space-y-6 text-lg leading-relaxed sm:text-xl lg:col-span-3">
              <p>
                Fine-tuning made ChatG&T more structurally reliable and almost eliminated the need for examples in the
                system prompt.
              </p>
              <p>
                On 60 unseen prompts, the fine-tuned model produced 52 schema-valid responses. The five-shot baseline
                produced 43. At the same time, the average input fell from approximately 2,576 tokens to 32.
              </p>
              <p className="text-signal">
                The model learned the form of ChatG&T more readily than the substance of its answers.
              </p>
            </div>
          </div>
        </section>

        <div className="grid border-l border-t border-outline sm:grid-cols-2 lg:grid-cols-4">
          <ResultFigure label="Schema-valid" note="Fine-tuned, compared with 43 / 60 prompted." value="52 / 60" />
          <ResultFigure label="Recurring input" note="Average prompt tokens, down from approximately 2,576." value="32" />
          <ResultFigure label="Full response" note="Fine-tuned, compared with 16 / 60 prompted." value="26 / 60" />
          <ResultFigure label="Generation time" note="Fine-tuned, compared with 3.92 seconds prompted." value="5.70s" />
        </div>

        <Section number="01 / 05" title="What we compared">
          <Prose>
            <p>
              The primary comparison used the same 1.5-billion-parameter base model in two configurations. The prompted
              system received a detailed system prompt with five worked examples. The fine-tuned system used the
              selected LoRA adapter and a minimal system prompt.
            </p>
            <p>
              Both answered the same 60 prompts, which had been withheld from training. Each prompt was attempted once.
              Responses were not repaired, regenerated, or manually corrected.
            </p>
            <p>
              A successful response had to do more than contain valid JSON. It needed to follow the required schema,
              answer the user&apos;s underlying question, express that answer through a coherent cocktail metaphor, and
              read like a plausible recipe.
            </p>
          </Prose>

        </Section>

        <Section number="02 / 05" title="The structure became reliable">
          <div className="grid border border-outline sm:grid-cols-2">
            <div className="border-b border-outline p-5 sm:border-b-0 sm:border-r sm:p-8">
              <p className="text-xs uppercase">Five-shot prompt</p>
              <p className="mt-12 text-5xl leading-none tracking-tighter sm:text-6xl">43 / 60</p>
              <p className="mt-4 text-sm">Schema-valid responses</p>
            </div>
            <div className="p-5 sm:p-8">
              <p className="text-xs uppercase text-signal">Fine-tuned</p>
              <p className="mt-12 text-5xl leading-none tracking-tighter text-signal sm:text-6xl">52 / 60</p>
              <p className="mt-4 text-sm">Schema-valid responses</p>
            </div>
          </div>

          <Prose className="mt-10">
            <p>
              Fine-tuning made the model more reliable at returning responses the product could render. It followed
              the required schema on 52 of 60 prompts, compared with 43 for the five-shot baseline.
            </p>
            <p>
              That is an improvement of 15 percentage points. Allowing for variation across the 60 prompts, the
              estimated improvement ranged from 1.7 to 28.3 percentage points and remained above zero. This gives us
              reasonable confidence that fine-tuning improved structural reliability in this test.
            </p>
            <p>
              This result is about format, not answer quality. A response can follow the schema and still contain poor
              advice.
            </p>
          </Prose>

          <blockquote className="mt-12 max-w-5xl border-l border-signal pl-5 text-lg leading-relaxed sm:pl-8 sm:text-xl">
            Fine-tuning taught the model the response contract: which fields to produce, how to organise them, and how
            the parts of a ChatG&T answer fit together.
          </blockquote>
        </Section>

        <Section number="03 / 05" title="Answer quality is harder to call">
          <Prose>
            <p>
              The automated evaluator rated the fine-tuned responses more highly for usefulness, metaphor, and recipe
              quality. However, these assessments were subjective, and the human review did not consistently agree.
              The apparent improvement in answer quality is therefore less certain than the improvement in structure.
            </p>
          </Prose>

          <div className="mt-10 border border-outline">
            <div className="grid grid-cols-3 border-b border-outline px-4 py-4 text-xs uppercase sm:px-6">
              <p>Criterion</p>
              <p>Prompted</p>
              <p className="text-signal">Fine-tuned</p>
            </div>
            {QUALITY_RESULTS.map((result) => (
              <div className="grid grid-cols-3 gap-4 border-b border-outline px-4 py-6 last:border-b-0 sm:px-6" key={result.label}>
                <div>
                  <p className="text-sm">{result.label}</p>
                  <p className="mt-2 hidden max-w-xs text-xs leading-relaxed text-muted sm:block">{result.note}</p>
                </div>
                <p className="text-xl tabular-nums sm:text-2xl">{result.prompted}</p>
                <p className="text-xl tabular-nums text-signal sm:text-2xl">{result.tuned}</p>
              </div>
            ))}
          </div>

          <div className="mt-12 grid gap-10 lg:grid-cols-2 lg:gap-16">
            <div>
              <p className="text-xs uppercase text-signal">Usefulness</p>
              <p className="mt-4 text-base leading-relaxed">
                The automated evaluator judged 29 of 60 fine-tuned responses useful, compared with 19 of 60 prompted
                responses. However, the human reviewer agreed with the evaluator in only 9 of 18 calibration cases.
                The result suggests an improvement, but does not establish that people would find the fine-tuned
                answers more useful.
              </p>
            </div>
            <div>
              <p className="text-xs uppercase text-signal">Recipe style</p>
              <p className="mt-4 text-base leading-relaxed">
                The fine-tuned model produced more acceptable recipes overall: 45 of 60, compared with 39 of 60. This
                advantage came from producing more correctly structured responses. Among schema-valid responses, the
                prompted model passed the recipe-style check slightly more often—91% compared with 87%. Fine-tuning
                increased the number of usable recipes, but did not improve recipe style itself.
              </p>
            </div>
          </div>

        </Section>

        <Section number="04 / 05" title="The long prompt disappeared">
          <div className="grid border border-outline lg:grid-cols-2">
            <div className="border-b border-outline p-5 sm:p-8 lg:border-b-0 lg:border-r">
              <p className="text-xs uppercase">Average input tokens</p>
              <div className="mt-12 flex items-end gap-4">
                <p className="text-4xl leading-none tracking-tighter sm:text-6xl">2,576</p>
                <p className="pb-1 text-xl text-signal sm:text-2xl">→ 32</p>
              </div>
              <p className="mt-5 max-w-md text-sm leading-relaxed">Approximately 98.8% fewer recurring input tokens.</p>
            </div>
            <div className="p-5 sm:p-8">
              <p className="text-xs uppercase">Timed generation</p>
              <div className="mt-12 flex items-end gap-4">
                <p className="text-4xl leading-none tracking-tighter sm:text-6xl">3.92s</p>
                <p className="pb-1 text-xl text-signal sm:text-2xl">→ 5.70s</p>
              </div>
              <p className="mt-5 max-w-md text-sm leading-relaxed">The shorter prompt did not make generation faster.</p>
            </div>
          </div>

          <Prose className="mt-10">
            <p>
              Fine-tuning allowed us to remove the five worked examples from every request because the adapter had
              learned the behaviour they demonstrated. This reduced the average input from approximately 2,576 tokens
              to 32, leaving more context available for the user&apos;s request.
            </p>
            <p>
              The shorter prompt did not make responses faster. The fine-tuned model took an average of 5.70 seconds
              to generate a response, compared with 3.92 seconds for the prompted model. Fine-tuning also required the
              upfront work of preparing data, training the adapter, and evaluating it.
            </p>
            <p className="text-muted">
              This latency result applies only to model generation in our experimental setup. It does not show that
              LoRA is generally slower or predict how either system would perform in production.
            </p>
          </Prose>
        </Section>

        <Section number="05 / 05" title="What fine-tuning changed">
          <blockquote className="max-w-5xl border-l border-signal pl-5 text-lg leading-relaxed sm:pl-8 sm:text-xl">
            Fine-tuning moved much of the ChatG&T behaviour out of a long system prompt and into the model.
          </blockquote>

          <Prose className="mt-10">
            <p>
              Fine-tuning clearly improved the structure of the responses, but we found weaker evidence that it
              improved their content.
            </p>
            <p>
              One possible explanation is the size of the base model. A 1.5-billion-parameter model may be capable of
              learning a consistent response format without being capable of producing consistently useful answers.
            </p>
            <p>
              We tested only one model size, so we cannot confirm that model capacity was the problem. The next step
              would be to repeat the experiment with a stronger base model. This would help us distinguish between the
              limits of the model and the limits of our training approach.
            </p>
          </Prose>

          <div className="mt-12 grid border border-outline lg:grid-cols-2">
            <div className="border-b border-outline p-5 sm:p-8 lg:border-b-0 lg:border-r">
              <p className="text-xs uppercase text-signal">The experiment establishes</p>
              <ul className="mt-8 space-y-5 text-sm leading-relaxed">
                <li>Fine-tuning improved first-attempt structural reliability.</li>
                <li>It removed almost all recurring prompt context.</li>
                <li>It was slower in the matched generation measurement.</li>
              </ul>
            </div>
            <div className="p-5 sm:p-8">
              <p className="text-xs uppercase">The experiment does not establish</p>
              <ul className="mt-8 space-y-5 text-sm leading-relaxed">
                <li>That fine-tuning generally produces better answers than prompting.</li>
                <li>That people would consistently prefer the fine-tuned responses.</li>
                <li>That these results generalise beyond this model and evaluation.</li>
              </ul>
            </div>
          </div>
        </Section>

        <footer className="border-t border-outline py-16 sm:py-24">
          <p className="text-xs uppercase text-signal">The result</p>
          <p className="mt-6 max-w-6xl text-2xl leading-tight tracking-tighter sm:text-4xl lg:text-5xl">
            Fine-tuning succeeded at the part we could measure most confidently: it made the interface reliable and
            removed the long prompt. <span className="text-signal">It did not establish that the answers were better.</span>
          </p>

          <nav aria-label="Continue reading" className="mt-16 grid border-l border-t border-outline sm:grid-cols-3">
            <Link
              className="group flex min-h-48 flex-col justify-between border-b border-r border-outline p-5 hover:bg-steel hover:text-concrete sm:p-6"
              href="/experiment"
            >
              <span className="text-xs uppercase">How it was tested</span>
              <span className="flex items-end justify-between gap-6 text-xl">
                Experiment <span aria-hidden="true" className="group-hover:text-signal">↗</span>
              </span>
            </Link>
            <Link
              className="group flex min-h-48 flex-col justify-between border-b border-r border-outline p-5 hover:bg-steel hover:text-concrete sm:p-6"
              href="/learning"
            >
              <span className="text-xs uppercase">What it taught us</span>
              <span className="flex items-end justify-between gap-6 text-xl">
                Learning <span aria-hidden="true" className="group-hover:text-signal">↗</span>
              </span>
            </Link>
            <a
              className="group flex min-h-48 flex-col justify-between border-b border-r border-outline p-5 hover:bg-steel hover:text-concrete sm:p-6"
              href="https://github.com/WillEtheridge/chatgandt/blob/main/experiments/evaluations/heldout-evaluation-v1-20260717-run01/analysis/primary-results.json"
              rel="noreferrer"
              target="_blank"
            >
              <span className="text-xs uppercase">Inspect the evidence</span>
              <span className="flex items-end justify-between gap-6 text-xl">
                Raw results <span aria-hidden="true" className="group-hover:text-signal">↗</span>
              </span>
            </a>
          </nav>
        </footer>
      </article>

      <aside className="grid border-t border-outline text-xs uppercase sm:grid-cols-2">
        <p className="border-b border-outline px-4 py-6 sm:border-b-0 sm:border-r sm:px-6">
          Evidence / Frozen 17 July 2026
        </p>
        <p className="px-4 py-6 leading-relaxed sm:px-6">60 unseen prompts / First attempts / No repairs</p>
      </aside>
    </main>
  );
}

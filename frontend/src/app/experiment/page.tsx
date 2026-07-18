import type { Metadata } from "next";
import Link from "next/link";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "ChatG&T — Experiment",
  description: "The ChatG&T experiment.",
};

const EXPERIMENT_SECTIONS = [
  { href: "#research-question", label: "The research question", number: "01" },
  { href: "#framing-the-experiment", label: "Framing the experiment", number: "02" },
  {
    href: "#establishing-the-technical-baseline",
    label: "Establishing the technical baseline",
    number: "03",
  },
  { href: "#fixing-the-evaluation-method", label: "Fixing the evaluation method", number: "04" },
  { href: "#building-the-supervised-dataset", label: "Building the supervised dataset", number: "05" },
  { href: "#creating-the-held-out-test", label: "Creating the held-out test", number: "06" },
  { href: "#training-the-adapters", label: "Training the adapters", number: "07" },
  { href: "#preparing-the-final-comparison", label: "Preparing the final comparison", number: "08" },
  { href: "#running-the-held-out-evaluation", label: "Running the held-out evaluation", number: "09" },
  {
    href: "#what-the-experiment-can-establish",
    label: "What the experiment can establish",
    number: "10",
  },
] as const;

export default function ExperimentPage() {
  return (
    <main className="min-h-screen bg-concrete text-steel">
      <SiteHeader activePath="/experiment" />

      <article className="mx-auto max-w-5xl px-4 pb-20 pt-12 sm:px-6 sm:pb-32 sm:pt-20 lg:max-w-7xl">
        <header className="pb-16 sm:pb-24">
          <h1 className="max-w-6xl text-4xl leading-none tracking-tighter sm:text-7xl lg:text-8xl">
            Experiment<span className="text-signal">.</span>
          </h1>

          <nav aria-label="Experiment contents" className="mt-12">
            <p className="text-xs uppercase text-signal">Contents</p>
            <ol className="mt-5 grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3 lg:grid-cols-5">
              {EXPERIMENT_SECTIONS.map((section) => (
                <li key={section.href}>
                  <Link className="flex gap-3 text-xs leading-relaxed hover:text-signal" href={section.href}>
                    <span className="text-signal">{section.number}</span>
                    <span>{section.label}</span>
                  </Link>
                </li>
              ))}
            </ol>
          </nav>
        </header>

        <section aria-labelledby="research-question" className="py-16 sm:py-24">
          <div className="grid gap-10 lg:grid-cols-4 lg:gap-16">
            <header>
              <p className="text-xs uppercase text-signal">01</p>
              <h2
                className="mt-4 text-3xl leading-tight tracking-tighter sm:text-4xl"
                id="research-question"
              >
                The research question
              </h2>
            </header>

            <div className="lg:col-span-3">
              <div className="max-w-3xl space-y-5 text-base leading-relaxed">
                <p>There are two main ways to get a language model to perform a specialised task:</p>
                <ul className="list-disc space-y-3 pl-5">
                  <li>Give it detailed instructions and examples in the prompt.</li>
                  <li>Fine-tune it on examples of the behaviour we want.</li>
                </ul>
                <p>We wanted to compare these approaches using the same small language model.</p>
              </div>

              <blockquote className="my-12 max-w-5xl border-l border-signal pl-5 text-lg leading-relaxed sm:pl-8 sm:text-xl">
                How does LoRA-based supervised fine-tuning compare with a strong five-shot prompt in producing
                schema-valid, useful, metaphorically coherent, and stylistically consistent ChatG&amp;T responses on
                unseen prompts, and what trade-offs does it introduce in prompt-token usage and latency?
              </blockquote>

              <div className="max-w-3xl space-y-5 text-base leading-relaxed">
                <p>
                  Put simply, we asked whether fine-tuning worked better than a well-developed prompt—and what each
                  approach required in input tokens and generation time.
                </p>
                <p>
                  ChatG&amp;T was the test case. Its responses needed to follow a fixed structure, answer the user well
                  and express that answer as a convincing cocktail recipe. This allowed us to measure structural
                  reliability separately from response quality.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section aria-labelledby="framing-the-experiment" className="py-16 sm:py-24">
          <div className="grid gap-10 lg:grid-cols-4 lg:gap-16">
            <header>
              <p className="text-xs uppercase text-signal">02</p>
              <h2
                className="mt-4 text-3xl leading-tight tracking-tighter sm:text-4xl"
                id="framing-the-experiment"
              >
                Framing the experiment
              </h2>
            </header>

            <div className="lg:col-span-3">
              <div className="max-w-3xl space-y-5 text-base leading-relaxed">
                <p>
                  To answer the question, we needed to compare prompting and fine-tuning in a way that showed what each
                  approach changed.
                </p>
                <p>We designed four systems using the same base model:</p>
              </div>

              <div className="mt-10 overflow-x-auto border border-outline">
                <table className="w-full min-w-lg text-left">
                  <thead className="border-b border-outline text-xs uppercase">
                    <tr>
                      <th className="px-4 py-4 sm:px-6">System</th>
                      <th className="px-4 py-4 sm:px-6">Model</th>
                      <th className="px-4 py-4 sm:px-6">ChatG&amp;T prompt</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b border-outline">
                      <td className="px-4 py-5 text-signal sm:px-6">A</td>
                      <td className="px-4 py-5 sm:px-6">Base model</td>
                      <td className="px-4 py-5 sm:px-6">None</td>
                    </tr>
                    <tr className="border-b border-outline">
                      <td className="px-4 py-5 text-signal sm:px-6">B</td>
                      <td className="px-4 py-5 sm:px-6">Base model</td>
                      <td className="px-4 py-5 sm:px-6">Five examples</td>
                    </tr>
                    <tr className="border-b border-outline">
                      <td className="px-4 py-5 text-signal sm:px-6">C</td>
                      <td className="px-4 py-5 sm:px-6">Fine-tuned model</td>
                      <td className="px-4 py-5 sm:px-6">None</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-5 text-signal sm:px-6">D</td>
                      <td className="px-4 py-5 sm:px-6">Fine-tuned model</td>
                      <td className="px-4 py-5 sm:px-6">Five examples</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="mt-10 max-w-3xl space-y-5 text-base leading-relaxed">
                <p>The main comparison was between B and C: a well-developed prompt versus fine-tuning.</p>
                <p>
                  We included A and D because B and C differ in two ways—the prompt and the fine-tuning. The additional
                  systems showed what happened with neither approach, each approach on its own, and both together.
                </p>
                <p>Before developing the systems, we also defined what a successful response required. It had to:</p>
                <ul className="list-disc space-y-3 pl-5">
                  <li>Follow the fixed JSON structure.</li>
                  <li>Answer the user’s request well.</li>
                  <li>Express the answer through a meaningful cocktail metaphor.</li>
                  <li>Read like a convincing cocktail recipe.</li>
                </ul>
                <p>A response passed only if it met all four requirements.</p>
                <p>
                  Finally, we set limits on what the experiment would cover. We focused on English-language,
                  single-turn, low-stakes prompts that could be answered using stable general knowledge. We excluded
                  live information, professional or emergency advice, tool use, long conversations and non-English
                  prompts.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section aria-labelledby="establishing-the-technical-baseline" className="py-16 sm:py-24">
          <div className="grid gap-10 lg:grid-cols-4 lg:gap-16">
            <header>
              <p className="text-xs uppercase text-signal">03</p>
              <h2
                className="mt-4 text-3xl leading-tight tracking-tighter sm:text-4xl"
                id="establishing-the-technical-baseline"
              >
                Establishing the technical baseline
              </h2>
            </header>

            <div className="lg:col-span-3">
              <div className="max-w-3xl space-y-5 text-base leading-relaxed">
                <p>
                  Before training anything, we needed a reliable model, a repeatable way to run it, and a fair
                  prompt-engineered baseline.
                </p>
                <p>
                  We selected Qwen2.5-1.5B-Instruct. It was small enough to train and deploy within the project’s
                  budget, supported LoRA, could already produce structured output, and had a permissive licence.
                </p>
                <p>
                  We then tested the complete LoRA process on rented GPU hardware. We confirmed that we could attach an
                  adapter, train it without changing the base model, save it, reload it and reproduce the same output.
                </p>
                <p>
                  Next, we built one inference system for the whole experiment. It recorded the prompt, raw response,
                  model and adapter, token counts, seed and generation time. We also built a strict validator for the
                  required JSON structure. Invalid responses were recorded as failures rather than repaired.
                </p>
                <p>
                  Finally, we developed the five-example prompt. We tested four versions on a separate set of 20
                  development prompts. Version 3 won the selection rule we had defined in advance. Version 4 performed
                  worse, so we stopped rather than continuing to revise the prompt.
                </p>
                <p>
                  Version 3 did not perform best on every measure when we confirmed it in the final runtime. We kept it
                  because it won the agreed selection process, not because it made the later fine-tuning comparison
                  easier.
                </p>
                <p>
                  At the end of this stage, the base model, runtime, measurement tools and prompt baseline were fixed.
                  Fine-tuning had not begun, and the final test prompts had not been created.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section aria-labelledby="fixing-the-evaluation-method" className="py-16 sm:py-24">
          <div className="grid gap-10 lg:grid-cols-4 lg:gap-16">
            <header>
              <p className="text-xs uppercase text-signal">04</p>
              <h2
                className="mt-4 text-3xl leading-tight tracking-tighter sm:text-4xl"
                id="fixing-the-evaluation-method"
              >
                Fixing the evaluation method
              </h2>
            </header>

            <div className="lg:col-span-3">
              <div className="max-w-3xl space-y-5 text-base leading-relaxed">
                <p>Before creating the training data, we decided exactly how the systems would be tested.</p>
                <p>
                  We planned a final test containing 60 prompts across five types of task: advice, explanation,
                  low-stakes emotional support, creative writing and short-form rewriting. The test would include
                  ordinary requests, unfamiliar subject areas and prompts designed to challenge the required format.
                  At this point, we defined the shape of the test but did not write the exact prompts.
                </p>
                <p>
                  We also fixed how each response would be evaluated. First, it would be checked automatically against
                  the JSON schema. If it passed, it would then be judged on the quality of the answer, the cocktail
                  metaphor and the recipe style. A response received a full pass only if every part succeeded.
                </p>
                <p>
                  The main comparison would be between the five-example prompt and the fine-tuned model. Their
                  responses would be compared without revealing which system had produced them. We also decided how to
                  record cases where one or both systems failed the structural check.
                </p>
                <p>
                  For every response, we would record the number of input tokens, the number of generated tokens and
                  the time taken by the model to generate it.
                </p>
                <p>
                  We knew that 60 prompts could not perfectly represent every possible user request. We therefore
                  decided in advance how to report the uncertainty around differences between the systems. We also
                  selected a fixed sample for the project author to review, so we could see how closely the automated
                  evaluator agreed with a human judgement.
                </p>
                <p>
                  Finally, we defined how the future test prompts would be checked against development and training
                  material. We also planned to compare the generated responses with examples each system had seen,
                  looking for suspicious reuse rather than assuming that every similarity proved memorisation.
                </p>
                <p>
                  At the end of this stage, the complete evaluation method was fixed. The training data had not been
                  created, the exact test prompts had not been written, and fine-tuning had not begun.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section aria-labelledby="building-the-supervised-dataset" className="py-16 sm:py-24">
          <div className="grid gap-10 lg:grid-cols-4 lg:gap-16">
            <header>
              <p className="text-xs uppercase text-signal">05</p>
              <h2
                className="mt-4 text-3xl leading-tight tracking-tighter sm:text-4xl"
                id="building-the-supervised-dataset"
              >
                Building the supervised dataset
              </h2>
            </header>

            <div className="lg:col-span-3">
              <div className="max-w-3xl space-y-5 text-base leading-relaxed">
                <p>
                  Once the evaluation method was fixed, we created the examples that would be used to fine-tune the
                  model.
                </p>
                <p>
                  The dataset contained 200 user prompts paired with complete ChatG&amp;T responses. It covered the same
                  five types of task defined for the experiment, with 40 examples of each.
                </p>
                <p>
                  Every response had to follow the JSON schema and pass a separate review of its answer, metaphor and
                  recipe style. Examples that did not pass were revised or replaced rather than included as training
                  targets.
                </p>
                <p>
                  We split the dataset into 160 training examples and 40 validation examples. Related versions of the
                  same situation were kept in the same split. This prevented the model from training on one version of
                  a scenario and then being validated on a close variation.
                </p>
                <p>
                  We also selected a 40-example pilot set from within the training data. This gave us a smaller dataset
                  for checking the training process before running the full adapter search.
                </p>
                <p>
                  We did not use Qwen’s responses or training performance to decide which examples to keep or change.
                  The exact final test prompts had not yet been written, so the dataset could not be designed around
                  the questions the model would later face.
                </p>
                <p>
                  At the end of this stage, the training data, validation data and pilot set were reviewed and frozen.
                  Only then did we begin creating the held-out test.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section aria-labelledby="creating-the-held-out-test" className="py-16 sm:py-24">
          <div className="grid gap-10 lg:grid-cols-4 lg:gap-16">
            <header>
              <p className="text-xs uppercase text-signal">06</p>
              <h2
                className="mt-4 text-3xl leading-tight tracking-tighter sm:text-4xl"
                id="creating-the-held-out-test"
              >
                Creating the held-out test
              </h2>
            </header>

            <div className="lg:col-span-3">
              <div className="max-w-3xl space-y-5 text-base leading-relaxed">
                <p>
                  After the training data and five-example prompt were frozen, we wrote the 60 prompts for the final
                  test.
                </p>
                <p>The set contained 12 prompts from each of the five task types. It included:</p>
                <ul className="list-disc space-y-3 pl-5">
                  <li>30 ordinary requests similar to the intended use of ChatG&amp;T.</li>
                  <li>
                    15 requests about photography, tabletop games and pottery—subjects deliberately excluded from the
                    training data.
                  </li>
                  <li>15 prompts designed to challenge the required behaviour or JSON format.</li>
                </ul>
                <p>
                  We also varied how the prompts were written. Some were questions, some were direct requests, and
                  others were statements or fragments. Some combined several requirements, while others included
                  specific constraints the response needed to follow.
                </p>
                <p>
                  We compared the 60 prompts with 231 prompts already used elsewhere in the project. The check found no
                  exact matches and no pairs with wording similar enough to trigger review.
                </p>
                <p>
                  We then reviewed the complete set. Every prompt needed to be clear, low-stakes, answerable without
                  external tools and suitable for evaluation.
                </p>
                <p>
                  No model responses were generated while the test was being created. The prompts were frozen before
                  fine-tuning began and could not be changed after we saw how the model performed.
                </p>
                <p>
                  This gave us a controlled final test that had remained separate from prompt development, dataset
                  creation and adapter training.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section aria-labelledby="training-the-adapters" className="py-16 sm:py-24">
          <div className="grid gap-10 lg:grid-cols-4 lg:gap-16">
            <header>
              <p className="text-xs uppercase text-signal">07</p>
              <h2
                className="mt-4 text-3xl leading-tight tracking-tighter sm:text-4xl"
                id="training-the-adapters"
              >
                Training the adapters
              </h2>
            </header>

            <div className="lg:col-span-3">
              <div className="max-w-3xl space-y-5 text-base leading-relaxed">
                <p>
                  We began with a small pilot using 40 training examples. Its purpose was to check that the complete
                  training process worked before moving to the full dataset.
                </p>
                <p>
                  The pilot completed successfully. The training and validation loss improved, the base model remained
                  unchanged, and the adapter could be saved and reloaded correctly.
                </p>
                <p>
                  We then tested the pilot adapter on ten development prompts. It changed the model’s responses, but
                  none followed the required schema. This showed that a technically successful training run did not
                  necessarily produce the behaviour we wanted.
                </p>
                <p>We moved on to a limited search of five full candidates. Each candidate tested a specific idea:</p>
                <ol className="list-decimal space-y-3 pl-5">
                  <li>Train on the complete dataset.</li>
                  <li>Train for longer.</li>
                  <li>Apply LoRA to more of the model’s attention layers.</li>
                  <li>Extend LoRA into both the attention and feed-forward layers.</li>
                  <li>
                    Give more training weight to the ingredient names and method steps, where much of the answer was
                    expressed.
                  </li>
                </ol>
                <p>
                  Within each training run, validation loss was used to choose the checkpoint. It was not used to decide
                  which candidate was best. That decision depended on the responses each candidate generated.
                </p>
                <p>
                  Every candidate answered the same ten development prompts. Their identities were hidden while the
                  responses were evaluated.
                </p>
                <p>A candidate was considered viable only if:</p>
                <ul className="list-disc space-y-3 pl-5">
                  <li>At least 8 of 10 responses followed the schema.</li>
                  <li>At least 7 of 10 passed the complete quality check.</li>
                  <li>Every task type contained at least one complete pass.</li>
                </ul>
                <p>None of the five candidates met all three requirements.</p>
              </div>

              <div className="mt-10 overflow-x-auto border border-outline">
                <table className="w-full min-w-lg text-left">
                  <thead className="border-b border-outline text-xs uppercase">
                    <tr>
                      <th className="px-4 py-4 sm:px-6">Candidate</th>
                      <th className="px-4 py-4 sm:px-6">Schema-valid</th>
                      <th className="px-4 py-4 sm:px-6">Complete passes</th>
                      <th className="px-4 py-4 sm:px-6">Task types represented</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b border-outline">
                      <td className="px-4 py-5 text-signal sm:px-6">1</td>
                      <td className="px-4 py-5 sm:px-6">7 / 10</td>
                      <td className="px-4 py-5 sm:px-6">3 / 10</td>
                      <td className="px-4 py-5 sm:px-6">2 / 5</td>
                    </tr>
                    <tr className="border-b border-outline">
                      <td className="px-4 py-5 text-signal sm:px-6">2</td>
                      <td className="px-4 py-5 sm:px-6">9 / 10</td>
                      <td className="px-4 py-5 sm:px-6">4 / 10</td>
                      <td className="px-4 py-5 sm:px-6">2 / 5</td>
                    </tr>
                    <tr className="border-b border-outline">
                      <td className="px-4 py-5 text-signal sm:px-6">3</td>
                      <td className="px-4 py-5 sm:px-6">10 / 10</td>
                      <td className="px-4 py-5 sm:px-6">6 / 10</td>
                      <td className="px-4 py-5 sm:px-6">5 / 5</td>
                    </tr>
                    <tr className="border-b border-outline">
                      <td className="px-4 py-5 text-signal sm:px-6">4</td>
                      <td className="px-4 py-5 sm:px-6">9 / 10</td>
                      <td className="px-4 py-5 sm:px-6">6 / 10</td>
                      <td className="px-4 py-5 sm:px-6">4 / 5</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-5 text-signal sm:px-6">5</td>
                      <td className="px-4 py-5 sm:px-6">9 / 10</td>
                      <td className="px-4 py-5 sm:px-6">4 / 10</td>
                      <td className="px-4 py-5 sm:px-6">3 / 5</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="mt-10 max-w-3xl space-y-5 text-base leading-relaxed">
                <p>
                  Candidate 3 came closest. Every response followed the schema, six passed the complete quality check,
                  and all five task types were represented. It missed the required quality threshold by one response.
                </p>
                <p>
                  Candidate 4 achieved a lower validation loss than Candidate 3, but did not produce better responses.
                  This reinforced why validation loss alone was not enough to select a model.
                </p>
                <p>
                  The search ended after the fifth candidate, as planned. We did not lower the quality standard or
                  train a sixth candidate after seeing the results.
                </p>
                <p>
                  No viable adapter was selected. Candidate 3 was the most informative candidate, but it was not a
                  winner.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section aria-labelledby="preparing-the-final-comparison" className="py-16 sm:py-24">
          <div className="grid gap-10 lg:grid-cols-4 lg:gap-16">
            <header>
              <p className="text-xs uppercase text-signal">08</p>
              <h2
                className="mt-4 text-3xl leading-tight tracking-tighter sm:text-4xl"
                id="preparing-the-final-comparison"
              >
                Preparing the final comparison
              </h2>
            </header>

            <div className="lg:col-span-3">
              <div className="max-w-3xl space-y-5 text-base leading-relaxed">
                <p>
                  None of the five adapters passed the product-quality gate. However, we still needed a fine-tuned
                  model to answer the original research question.
                </p>
                <p>
                  We chose Candidate 3 before generating any responses from the held-out test. It was the most useful
                  candidate for understanding what fine-tuning had changed:
                </p>
                <ul className="list-disc space-y-3 pl-5">
                  <li>All ten development responses followed the schema.</li>
                  <li>Six of ten passed the complete quality check.</li>
                  <li>It was the only candidate with complete passes across all five task types.</li>
                  <li>
                    It used a simpler adapter than Candidate 4, which achieved the same number of complete passes.
                  </li>
                </ul>
                <p>
                  Candidate 3 was not accepted as a product-quality model. It was included as a diagnostic model:
                  something we could evaluate to understand the effect of the fine-tuning work.
                </p>
                <p>This gave us the four systems for the final experiment:</p>
              </div>

              <div className="mt-10 overflow-x-auto border border-outline">
                <table className="w-full min-w-lg text-left">
                  <thead className="border-b border-outline text-xs uppercase">
                    <tr>
                      <th className="px-4 py-4 sm:px-6">System</th>
                      <th className="px-4 py-4 sm:px-6">Model</th>
                      <th className="px-4 py-4 sm:px-6">Prompt</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b border-outline">
                      <td className="px-4 py-5 text-signal sm:px-6">A</td>
                      <td className="px-4 py-5 sm:px-6">Base model</td>
                      <td className="px-4 py-5 sm:px-6">Minimal prompt</td>
                    </tr>
                    <tr className="border-b border-outline">
                      <td className="px-4 py-5 text-signal sm:px-6">B</td>
                      <td className="px-4 py-5 sm:px-6">Base model</td>
                      <td className="px-4 py-5 sm:px-6">Five-example prompt</td>
                    </tr>
                    <tr className="border-b border-outline">
                      <td className="px-4 py-5 text-signal sm:px-6">C</td>
                      <td className="px-4 py-5 sm:px-6">Candidate 3</td>
                      <td className="px-4 py-5 sm:px-6">Minimal prompt</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-5 text-signal sm:px-6">D</td>
                      <td className="px-4 py-5 sm:px-6">Candidate 3</td>
                      <td className="px-4 py-5 sm:px-6">Five-example prompt</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="mt-10 max-w-3xl space-y-5 text-base leading-relaxed">
                <p>
                  The held-out results could describe how Candidate 3 behaved, but they could not turn it into a
                  winner. We would not use the final test to restart training, lower the quality gate or choose a
                  different adapter.
                </p>
                <p>
                  At the end of this stage, the model, adapter and prompt used by every system were fixed. The held-out
                  evaluation could now begin.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section aria-labelledby="running-the-held-out-evaluation" className="py-16 sm:py-24">
          <div className="grid gap-10 lg:grid-cols-4 lg:gap-16">
            <header>
              <p className="text-xs uppercase text-signal">09</p>
              <h2
                className="mt-4 text-3xl leading-tight tracking-tighter sm:text-4xl"
                id="running-the-held-out-evaluation"
              >
                Running the held-out evaluation
              </h2>
            </header>

            <div className="lg:col-span-3">
              <div className="max-w-3xl space-y-5 text-base leading-relaxed">
                <p>We ran the final experiment once.</p>
                <p>
                  Each of the four systems answered the same 60 held-out prompts, producing 240 responses in total.
                </p>
                <p>
                  The complete run used one RTX 4090, the same base model and tokenizer, and the generation settings
                  and seed policy fixed earlier. Each system received one attempt at every prompt.
                </p>
                <p>
                  Once generation began, every response counted. Invalid JSON, incomplete answers and factual mistakes
                  were results—not reasons to try again. We did not repair, regenerate or replace any output.
                </p>
                <p>We then applied the evaluation process defined before training:</p>
                <ol className="list-decimal space-y-3 pl-5">
                  <li>All 240 responses were checked against the JSON schema.</li>
                  <li>
                    Every schema-valid response was evaluated for answer quality, metaphor and recipe style.
                  </li>
                  <li>
                    The prompt-engineered and fine-tuned responses were compared without revealing which system had
                    produced them.
                  </li>
                  <li>
                    The project author reviewed the fixed human sample so we could measure agreement with the
                    automated evaluator.
                  </li>
                  <li>Input tokens, generated tokens and generation time were recorded for every response.</li>
                  <li>
                    The responses were compared with examples the systems had seen, looking for suspicious reuse.
                  </li>
                  <li>The final differences and uncertainty ranges were calculated.</li>
                </ol>
                <p>
                  All 240 scheduled responses completed. The results could describe how the systems performed, but
                  they could not be used to retrain the model, change the prompt or revise the evaluation method.
                </p>
                <p>
                  The experiment was complete. The systems had been fixed, the test had remained separate, and every
                  first attempt had been retained.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section aria-labelledby="what-the-experiment-can-establish" className="py-16 sm:py-24">
          <div className="grid gap-10 lg:grid-cols-4 lg:gap-16">
            <header>
              <p className="text-xs uppercase text-signal">10</p>
              <h2
                className="mt-4 text-3xl leading-tight tracking-tighter sm:text-4xl"
                id="what-the-experiment-can-establish"
              >
                What the experiment can establish
              </h2>
            </header>

            <div className="lg:col-span-3">
              <div className="max-w-3xl space-y-5 text-base leading-relaxed">
                <p>This was a controlled comparison, not a universal test of prompting and fine-tuning.</p>
                <p>The experiment can tell us:</p>
                <ul className="list-disc space-y-3 pl-5">
                  <li>How the four systems performed on the same 60 held-out prompts.</li>
                  <li>How reliably each system followed the required JSON structure.</li>
                  <li>How the evaluated responses compared in answer quality, metaphor and recipe style.</li>
                  <li>How many input tokens each approach required.</li>
                  <li>How long generation took in the measured setup.</li>
                  <li>What Candidate 3 changed in this particular small model.</li>
                </ul>
                <p>The experiment cannot tell us:</p>
                <ul className="list-disc space-y-3 pl-5">
                  <li>Whether the same result would appear with a larger or different model.</li>
                  <li>Whether the 60 authored prompts represent every possible user request.</li>
                  <li>Whether one automated evaluator represents general human preference.</li>
                  <li>Whether one response per prompt captures every way the systems could behave.</li>
                  <li>
                    Whether the measured generation time represents complete production latency or serving cost.
                  </li>
                  <li>Whether prompting or fine-tuning is always the better approach.</li>
                </ul>
                <p>
                  Candidate 3 remained below the product-quality gate. The final evaluation measured what the adapter
                  had changed, but it did not make the candidate suitable for deployment.
                </p>
                <p>These limits do not make the result less useful. They define what the evidence supports:</p>
              </div>

              <blockquote className="my-12 max-w-5xl border-l border-signal pl-5 text-lg leading-relaxed sm:pl-8 sm:text-xl">
                This is what happened in the ChatG&amp;T experiment under these conditions.
              </blockquote>

              <div className="max-w-3xl space-y-5 text-base leading-relaxed">
                <p>The Results page shows what we found within those limits.</p>
              </div>
            </div>
          </div>
        </section>

        <footer className="pb-16 sm:pb-24">
          <nav aria-label="Continue reading" className="grid border-l border-t border-outline sm:grid-cols-2">
            <Link
              className="group flex min-h-48 flex-col justify-between border-b border-r border-outline p-5 hover:bg-steel hover:text-concrete sm:p-6"
              href="/results"
            >
              <span className="text-xs uppercase">What happened</span>
              <span className="flex items-end justify-between gap-6 text-xl">
                Results <span aria-hidden="true" className="group-hover:text-signal">↗</span>
              </span>
            </Link>
            <Link
              className="group flex min-h-48 flex-col justify-between border-b border-r border-outline p-5 hover:bg-steel hover:text-concrete sm:p-6"
              href="/learning"
            >
              <span className="text-xs uppercase">What the project taught us</span>
              <span className="flex items-end justify-between gap-6 text-xl">
                Learning <span aria-hidden="true" className="group-hover:text-signal">↗</span>
              </span>
            </Link>
          </nav>
        </footer>
      </article>
    </main>
  );
}

import type { Metadata } from "next";
import Link from "next/link";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "ChatG&T — Learning",
  description: "What we learned while designing, training, evaluating, and deploying ChatG&T.",
};

const LEARNING_SECTIONS = [
  {
    stage: "Framing the question",
    title: "A useful research question separates different kinds of success",
    paragraphs: [
      "We learned that asking whether fine-tuning makes a model ‘better’ is too vague.",
      "We learned this by considering responses that succeeded in one way but failed in another. A response could follow the correct format while giving poor advice, or give a useful answer that the website could not display. A system could also use fewer tokens while taking longer to respond.",
      "We therefore measured structure, usefulness, metaphor, recipe quality, prompt length, and speed separately.",
    ],
  },
  {
    stage: "Designing the experiment",
    title: "A fair comparison must show everything that changed",
    paragraphs: [
      "We learned that comparing a prompted base model directly with a minimally prompted fine-tuned model does not explain why their responses differ.",
      "We learned this by noticing that the comparison changed both the model and the prompt. We added two more systems so we could test base and fine-tuned models with both short and detailed prompts.",
      "We also tested four versions of the detailed prompt. This gave fine-tuning a strong baseline rather than an easy one.",
    ],
  },
  {
    stage: "Building the baseline",
    title: "The model, prompt, and runtime form one system",
    paragraphs: [
      "We learned that a model name does not fully describe what produces a response.",
      "We learned this when one runtime silently added its own instructions, and when the model placed otherwise valid JSON inside Markdown code blocks that the website could not use. We also found that shortening the detailed prompt reduced its quality.",
      "The prompt, chat template, runtime settings, tokenizer, and output handling all affected the result.",
    ],
  },
  {
    stage: "Creating the data",
    title: "A good dataset needs more than the right number of examples",
    paragraphs: [
      "We learned that reaching 200 examples did not make the dataset complete.",
      "We learned this by checking its coverage, quality, repetition, token lengths, and recipe variety. An audit found seven examples that were too close to earlier work or to one another. Replacing them then accidentally removed the only recipes with seven and eight ingredients.",
      "A small change to a few examples could alter the balance of the whole dataset.",
    ],
  },
  {
    stage: "Training the model",
    title: "Successful training does not guarantee useful behaviour",
    paragraphs: [
      "We learned that a model can improve during training without showing the behaviour we want.",
      "We learned this when the first adapter trained correctly, reloaded correctly, and achieved lower validation loss, but produced no correctly structured responses on ten development prompts.",
      "Later candidates produced 7, then 9, then 10 correctly structured responses out of 10. Complete successes improved more slowly: from 3, to 4, to 6. The model learned the ChatG&T format before it reliably learned to give good answers inside it.",
    ],
  },
  {
    stage: "Evaluating the systems",
    title: "Some results are clearer than others",
    paragraphs: [
      "We learned that response structure can be measured more confidently than answer quality.",
      "We learned this during the final evaluation of 240 first responses. The prompted system produced 43 correctly structured responses and 16 complete successes. The fine-tuned system produced 52 correctly structured responses and 26 complete successes.",
      "Structure could be checked directly. Usefulness required judgment. A human reviewer and the automated evaluator usually agreed about recipe style, but agreed on only half of the underlying-answer decisions.",
    ],
  },
  {
    stage: "Interpreting the result",
    title: "Fine-tuning changes several trade-offs at once",
    paragraphs: [
      "We learned that fine-tuning cannot be described with one score.",
      "We learned this when it improved structural reliability and reduced the average input from about 2,576 tokens to 32, but increased generation time from 3.92 to 5.70 seconds.",
      "We also found that adding the detailed prompt to the fine-tuned model reduced complete successes from 26 to 21. Prompted and learned instructions did not simply add together.",
    ],
  },
  {
    stage: "Operating the infrastructure",
    title: "Running the infrastructure can take more work than training",
    paragraphs: [
      "We learned that the training loop is only a small part of a real machine-learning experiment.",
      "We learned this when GPUs with enough memory still failed because of incompatible drivers, and when machines created from the correct container image failed while the provider’s official template worked.",
      "The first three candidate runners used 113 seconds and about one cent of compute. The complete session cost about twelve cents because provisioning, installation, downloads, checks, transfers, and cleanup took longer than training.",
    ],
  },
  {
    stage: "Deploying the experience",
    title: "Deployment is a new technical environment",
    paragraphs: [
      "We learned that putting a trained model online is not simply a matter of copying the training files.",
      "We learned this when the adapter contained a path that existed only on the training machine. We replaced that path for publication while keeping the learned weights unchanged.",
      "ZeroGPU also used a different PyTorch version and did not provide a GPU until a request arrived. The private service credential had to remain on the server rather than being sent to the browser. Deployment introduced its own compatibility, security, and failure boundaries.",
    ],
  },
  {
    stage: "Looking back",
    title: "Rigour includes knowing when to stop",
    paragraphs: [
      "We learned that more process does not always produce better evidence.",
      "We learned this when an early audit produced 41,957 possible matches for review despite finding no automatic failures. The process had become larger than the risk it was meant to control, so we preserved the failed attempt and replaced it with a smaller audit.",
      "We applied the same discipline to training. Our strongest candidate achieved six complete successes when the required minimum was seven. Two more candidates also failed, so we stopped after five instead of lowering the target or continuing until something passed.",
    ],
  },
  {
    stage: "Working autonomously",
    title: "Tools, skills, and boundaries make real autonomy possible",
    paragraphs: [
      "We learned that Codex can complete a complex workflow autonomously when it has tools to act, skills that explain how to use them, and clear limits on what it may change.",
      "We learned this by giving Codex access to Runpod through its CLI, along with the project’s Runpod skills and a fixed experimental plan. Codex provisioned the GPUs, recovered from failed machines and incompatible drivers, ran and monitored all five training candidates, verified the results, retrieved the evidence, and stopped the billing.",
      "It did not simply follow a prepared list of commands. It handled unexpected problems while keeping the model, data, budget, and experimental rules unchanged.",
    ],
  },
] as const;

export default function LearningPage() {
  return (
    <main className="min-h-screen bg-concrete text-steel">
      <SiteHeader activePath="/learning" />

      <article className="mx-auto max-w-5xl px-4 pb-20 pt-12 sm:px-6 sm:pb-32 sm:pt-20 lg:max-w-7xl">
        <header className="pb-16 sm:pb-24">
          <p className="text-xs uppercase text-signal">Learning / From question to deployment</p>
          <h1 className="mt-6 max-w-6xl text-4xl leading-none tracking-tighter sm:text-7xl lg:text-8xl">
            What the work <span className="text-signal">taught us.</span>
          </h1>
          <div className="mt-12 grid gap-6 border-t border-outline pt-6 lg:grid-cols-4 lg:gap-12">
            <p className="text-xs uppercase">How we learned</p>
            <div className="max-w-3xl space-y-5 text-lg leading-relaxed lg:col-span-3">
              <p>
                ChatG&amp;T produced more than a result. Each stage changed how we understood the model, the experiment,
                and the work around them.
              </p>
              <p>
                These are the lessons we carried forward—and the moments that made us learn them.
              </p>
            </div>
          </div>
        </header>

        <ol className="border-b border-outline">
          {LEARNING_SECTIONS.map((section, index) => {
            const number = String(index + 1).padStart(2, "0");
            const id = `learning-${number}`;

            return (
              <li className="border-t border-outline py-16 sm:py-24" key={section.title}>
                <section aria-labelledby={id} className="grid gap-10 lg:grid-cols-4 lg:gap-16">
                  <header>
                    <p className="text-xs uppercase text-signal">{number} / 11</p>
                    <p className="mt-4 text-xs uppercase text-muted">{section.stage}</p>
                  </header>
                  <div className="lg:col-span-3">
                    <h2 className="max-w-4xl text-3xl leading-tight tracking-tighter sm:text-4xl" id={id}>
                      {section.title}
                    </h2>
                    <div className="mt-8 max-w-3xl space-y-5 text-base leading-relaxed">
                      {section.paragraphs.map((paragraph, paragraphIndex) => (
                        <p className={paragraphIndex === 0 ? "text-lg text-signal sm:text-xl" : undefined} key={paragraph}>
                          {paragraph}
                        </p>
                      ))}
                    </div>
                  </div>
                </section>
              </li>
            );
          })}
        </ol>

        <footer className="py-16 sm:py-24">
          <p className="text-xs uppercase text-signal">Continue exploring</p>
          <nav aria-label="Continue reading" className="mt-8 grid border-l border-t border-outline sm:grid-cols-2">
            <Link
              className="group flex min-h-48 flex-col justify-between border-b border-r border-outline p-5 hover:bg-steel hover:text-concrete sm:p-6"
              href="/experiment"
            >
              <span className="text-xs uppercase">How the work was designed</span>
              <span className="flex items-end justify-between gap-6 text-xl">
                Experiment <span aria-hidden="true" className="group-hover:text-signal">↗</span>
              </span>
            </Link>
            <Link
              className="group flex min-h-48 flex-col justify-between border-b border-r border-outline p-5 hover:bg-steel hover:text-concrete sm:p-6"
              href="/results"
            >
              <span className="text-xs uppercase">What the evidence showed</span>
              <span className="flex items-end justify-between gap-6 text-xl">
                Results <span aria-hidden="true" className="group-hover:text-signal">↗</span>
              </span>
            </Link>
          </nav>
        </footer>
      </article>

      <aside className="grid border-t border-outline text-xs uppercase sm:grid-cols-2">
        <p className="border-b border-outline px-4 py-6 sm:border-b-0 sm:border-r sm:px-6">
          Reflection / 11 stages
        </p>
        <p className="px-4 py-6 leading-relaxed sm:px-6">What changed / How we learned it / What transfers</p>
      </aside>
    </main>
  );
}

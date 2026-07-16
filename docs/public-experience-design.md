# ChatG&T Public Experience Design

## Status

This document records the agreed design baseline for the eventual ChatG&T public web experience. It defines the experience structure and interaction flows before visual design or implementation.

It is not a frozen implementation specification. Exact copy, visual design, deployment behaviour, and evidence-dependent Lab and Results content remain open until the relevant project work is complete.

Consequential public-experience decisions are recorded separately in [Public experience decisions](public-experience-decisions.md), so this work does not interfere with the active experimental decision log.

## Experience purpose

The public experience has two jobs:

1. let visitors enjoy ChatG&T as a useful novelty interaction; and
2. make the comparison between prompt engineering and fine-tuning understandable through participation and transparent explanation.

The cocktail-bar concept should shape the experience without obscuring the answer or the experiment. The public site should feel like entering a small, intelligent cocktail bar rather than operating a machine-learning dashboard.

## Experience principles

- Lead with the product experience; reveal the experiment as visitors become curious.
- Render model JSON as an accessible cocktail recipe, not as a developer object or chat bubble.
- Keep the Spirit Guide single-turn and low-stakes rather than implying a general-purpose conversational assistant.
- Preserve usefulness and reading clarity beneath the cocktail presentation.
- Communicate cold starts and failures honestly without using false progress.
- Keep the controlled evaluation distinct from playful public interactions.
- Do not collect or aggregate Tasting Room guesses as research evidence.
- Make negative, mixed, tied, and inconclusive experimental results as presentable as a clear fine-tuning win.
- Use technical detail progressively instead of confronting every visitor with it.

## Visual direction

The visual direction is **typographic brutalist mixology**: experimental, direct, clean, industrial, and future-facing. Typography, layout, copy, and interaction form the complete identity.

“Concrete” and “steel” describe the palette and attitude of the system. They do not call for photographed, illustrated, or simulated materials. Glass is not a visual motif.

### Typography

Neue Montreal Mono is the chosen typeface for the public experience, subject to obtaining and complying with the appropriate web licence before deployment.

One family should carry the interface through:

- large changes of scale and weight;
- exposed alignment and deliberate spacing;
- compact uppercase labels;
- tabular measurements, identifiers, and results;
- punctuation, numerals, coding ligatures, and boxed glyph treatments; and
- restrained italics where a human or reflective note needs distinction.

Monospaced body copy requires controlled line lengths and generous leading. Readability remains more important than preserving a display treatment at every size.

### Graphic vocabulary

The graphic system is limited to:

- type;
- whitespace;
- hard rules and visible grids;
- flat colour fields;
- glyphs, brackets, arrows, slashes, blocks, and counters;
- alignment and deliberate misalignment; and
- typographic motion.

For example:

```text
POUR_01
////////////////
MIXING
■■■■■■□□□□
```

The initial system does not use photography, illustration, decorative imagery, a separate icon set, material textures, shadows, ornamental three-dimensional assets, or simulated glass and concrete effects. A word or typeface glyph should perform an interface function wherever it remains clear and accessible.

Brutalism comes from exposed structure and directness rather than awkward interaction. Cocktail character comes from the content, measurements, labels, and language rather than literal drink imagery.

### Colour

The palette avoids pure black and pure white. It uses a warm concrete neutral against a cooler dark steel neutral, with intermediate tones for fields, rules, metadata, and inactive states.

The working starting palette is:

```text
CONCRETE_LIGHT   #D7D5CD   Primary background
CONCRETE_MID     #B8B6AF   Secondary fields and inactive states
STEEL_MID        #555C5E   Rules and metadata
STEEL_DARK       #292F30   Primary type and inverted fields
```

Normal and inverted fields provide the primary emphasis mechanism:

```text
NORMAL   concrete field / steel type
ACTIVE   steel field / concrete type
```

These values remain subject to rendered state-distinction checks. The mid-steel value was darkened from the initial `#687072` after browser validation found that the original provided only 3.44:1 contrast for small metadata against concrete-light; `#555C5E` provides approximately 4.64:1.

No accent colour is part of the initial direction. A functional signal colour may be introduced later only if error, success, focus, comparison identity, or another state cannot be communicated clearly and accessibly through type, structure, and concrete/steel inversion alone.

### Motion

Motion, where useful, is typographic and structural: counters advancing, glyph bars filling, labels replacing one another, hard masks revealing content, or text reflowing during a system reveal. It must not pretend to report progress the application cannot measure, and a complete reduced-motion equivalent is required.

## Information architecture

The public experience contains five principal pages:

1. **Spirit Guide** — use the selected production system.
2. **Tasting Room** — try to identify the fine-tuned response in a blinded comparison.
3. **Free Pour** — write instructions for the base model and compare it with the fine-tuned model.
4. **The Lab** — understand the experiment and its method.
5. **Results** — understand what happened and what was learned.

These form three broad modes:

- **Use it:** Spirit Guide.
- **Play with it:** Tasting Room and Free Pour.
- **Understand it:** The Lab and Results.

### Global navigation

Desktop navigation should expose all five destinations in a compact persistent header:

`Spirit Guide · Tasting Room · Free Pour · The Lab · Results`

The ChatG&T wordmark links to the Spirit Guide homepage. The active page is clearly marked. On mobile, a conventional Menu control opens a simple full-width navigation panel. Cocktail-menu styling may add character, but navigation must remain recognisable and accessible.

Results should not be presented as a substantive public destination before formal results exist. Whether it is hidden entirely or shown as unavailable during private development is an implementation decision.

Contextual calls to action connect related experiences without replacing global navigation.

## Shared interaction language

### Prompt scope

Public prompts retain the project's intended scope: English-language, single-turn, low-stakes requests that can be answered concisely without live information or external tools. The interface should communicate that scope quietly and clearly.

### Recipe response

Every schema-valid ChatG&T response uses one shared recipe presentation:

1. cocktail title;
2. ingredients with aligned amounts and units;
3. numbered method steps; and
4. a visually distinct garnish.

The component optimises for reading and accessibility. It does not expose raw JSON by default. The Lab may deliberately offer a recipe/JSON view toggle for explanation.

### Waiting

Waiting states may use cocktail language, but only to describe real states. Appropriate messages include:

- Calling your Spirit Guide…
- The model is waking up… when a cold start is actually known;
- Mixing your answer…; and
- Adding the garnish… when output is being processed.

An indeterminate animation may provide personality, but the application must not simulate measurable progress it does not have. An unusually long wait should be acknowledged and cancellable.

### Public data boundary

The application does not persist or aggregate Tasting Room guesses. Public guesses do not enter the formal evaluation or select a winning system.

No account or permanent user-visible history is planned. Free Pour iteration history may exist only within the current browser session. Operational logging, prompt retention, privacy copy, and infrastructure-level data handling must be defined before deployment; this document does not claim that network requests create no operational logs.

## Spirit Guide

### Purpose

Deliver the finished ChatG&T interaction immediately and simply.

### Entry

The Spirit Guide is the homepage rather than sitting behind a separate marketing screen. It presents:

- a concise proposition;
- a prominent multiline prompt field;
- several suggested prompts demonstrating appropriate breadth; and
- a restrained experimental and low-stakes notice.

Suggested prompts populate the field for inspection and editing rather than submitting immediately.

### Compose and submit

The prompt field behaves like placing an order rather than opening a chat conversation. It grows with its content. Enter creates a new line, while a clearly labelled control submits; a keyboard shortcut may also be supported.

The working primary action is **Mix it**.

After submission, the prompt remains visible, input is temporarily disabled, and a response region opens below it. Scrolling or focus movement should be gentle and predictable.

### Waiting and reveal

The interface communicates cold start, generation, and processing states honestly. Unless the serving architecture can stream validated structured content, the complete recipe appears only after a valid response has been received. Partial JSON tokens should not be shown to visitors.

### Continue

After a response, the primary options are:

- **Mix another** — clear the prompt and return focus to the composer; and
- **Adjust my order** — edit the existing prompt and generate again.

A contextual link invites curious visitors into the Tasting Room.

The initial experience excludes follow-up conversation, ratings, public feedback, accounts, permanent history, and sharing features.

### Failure behaviour

Service unavailability, timeout, and malformed model output are distinct states. All preserve the visitor's prompt and offer a clear recovery action. The product may use a retry policy for serving reliability, but that policy must be disclosed separately from the no-repair, no-retry formal evaluation. The exact retry rule remains deferred.

### Flow

`arrive → enter an order → mix → read the recipe → adjust or start again`

## Tasting Room

### Purpose

Let visitors experience the difference between prompt engineering and fine-tuning by guessing which response was fine-tuned.

This is a participatory explanation, not public preference research.

### Entry

The page leads with the challenge **Can you spot the fine-tune?** It explains in plain language that one response comes from the base model following the frozen five-example prompt and the other from the fine-tuned model without detailed ChatG&T instructions.

The page states that the visitor's guess is not recorded.

### Choose a tasting

The visitor writes a prompt or selects a suggested prompt, then chooses **Start the tasting**.

### Generate and conceal

Systems B and C generate concurrently. The interface:

- shows two equivalent concealed tasting positions;
- does not expose which response finishes first;
- does not expose latency, tokens, or system-specific progress;
- waits until both responses are ready before showing either; and
- randomly assigns them to Sample A and Sample B.

Both use the same recipe component. They appear side by side where space permits and as clearly labelled stacked samples on smaller screens.

### Guess

The visitor answers **Which sample was fine-tuned?** with one of:

- Sample A;
- Sample B; or
- Can't tell.

Can't tell is a genuine answer, not a failure. The Tasting Room does not also ask which response the visitor prefers; identification and preference are different questions.

### Reveal

After selection, the guess is fixed for that tasting and both identities are revealed simultaneously. Each response receives a neutral **Fine-tuned** or **Prompt-engineered** label. The interface acknowledges the guess without implying that the fine-tuned response is inherently better.

An optional disclosure explains how the two responses were made. Any request-specific latency or token details appear only after reveal and must not be confused with the formal measured results.

### Continue

The visitor may:

- taste another prompt;
- carry the current user prompt into Free Pour; or
- visit The Lab.

### Failure behaviour

A tasting proceeds only when both samples are available and suitable for presentation. If either side fails, the application does not expose the other response or reveal which system failed. It preserves the prompt and offers to retry the complete tasting.

### Flow

`choose a prompt → generate two concealed samples → compare → guess → reveal → learn → taste again or continue to Free Pour`

## Free Pour

### Purpose

Let visitors write instructions for the untrained base model, compare the result with the fine-tuned model, and iteratively explore the difference between prompting and training.

### Entry

The identities are visible from the beginning. The working proposition is:

> Give the base model your own instructions and see how it compares with the fine-tuned house model.

### Set the user prompt

The visitor supplies the underlying request both systems will answer. It may be written directly, selected from a suggestion, or carried from the Tasting Room.

After the first comparison, the user prompt remains fixed during an instruction-refinement session. Changing it starts a new pour and resets both systems' responses.

### Write instructions

A separate editor labelled **Your instructions for the base model** accepts the visitor's system-level instructions in ordinary language.

Planned starting options are:

- start from scratch with empty instructions;
- load a short editable head start; and
- load the exact frozen experimental baseline as an advanced option.

The editor exposes approximate instruction length or input-token usage so the recurring cost of more elaborate prompting is tangible. Exact controls and starter copy remain deferred.

### First comparison

The working initial action is **Pour both**. It generates:

- **Your Pour:** base model plus the visitor's instructions; and
- **House Pour:** fine-tuned model without detailed ChatG&T instructions.

Both receive the same user prompt. Their identities are never concealed.

### Non-recipe output

Free Pour expects instructions to fail sometimes. A schema-valid response uses the normal recipe component. A generated response that does not hold the ChatG&T structure appears safely as escaped plain text under an **Unmixed output** label, distinct from timeout or service failure.

Malformed output is not silently repaired or automatically retried in this exploratory flow because it is relevant evidence about the visitor's instructions.

### Compare and refine

The interface helps the visitor consider:

- recipe validity;
- instruction/input tokens;
- output tokens;
- underlying usefulness;
- metaphorical coherence; and
- recipe-style execution.

It does not assign an automatic subjective quality score.

The visitor edits the instructions and selects **Remix my pour**. Subsequent iterations regenerate only Your Pour; the original House Pour remains fixed as a stable reference. Prompted attempts may appear as numbered pours within the current browser session, with no account or permanent history.

### Explain

An expandable explanation distinguishes context instructions from learned behaviour, recurring prompt cost from one-time training effort, and individual demonstrations from the formal evaluation.

### Continue

The visitor may keep refining, start a new user prompt, load the experimental baseline, visit The Lab, or return to the Tasting Room.

### Flow

`choose a user prompt → write instructions → pour both → compare → refine instructions → regenerate the base response → learn why the systems differ`

## The Lab

### Purpose

Explain how the experiment works and establish trust in its method. The Lab presents the method, not the eventual conclusion.

### Narrative

The page follows this sequence:

1. **Research question** — whether a strong prompt or fine-tuning produces better ChatG&T behaviour and what efficiency trade-offs result.
2. **Four systems** — the two-by-two base/fine-tuned and no-prompt/five-shot design, with B versus C emphasised.
3. **Successful pour** — recipe view and raw JSON demonstrate why structure and quality are separate.
4. **Training process** — author, review, split, train a LoRA adapter, select, and freeze.
5. **Fair test** — freeze systems, author unseen prompts, generate, validate, judge blindly, reveal, and analyse.
6. **Measurements** — reliability, quality, blinded preference, and efficiency.
7. **Boundaries** — the small model, defined prompt population, deployment-specific latency, safety scope, and separation of public demonstrations from formal evidence.
8. **Next destinations** — Results, Spirit Guide, Free Pour, Tasting Room, and detailed project material.

### Interaction

The four-system comparison and measurement explanations may be selectable. Technical material appears through progressive disclosures. A lightweight sticky section navigator and linkable URL fragments support the long-form page. Core content must remain accessible without animation or model calls.

Detailed Lab content remains provisional until the main experimental work establishes the final assets, costs, failures, and decisions worth explaining.

### Flow

`understand the question → meet the systems → define success → see how training worked → understand the evaluation → inspect the boundaries → explore the evidence or try it yourself`

## Results

### Purpose

Answer the research question clearly, honestly, and accessibly using the frozen formal evidence. Results describe what happened and what was learned; they do not incorporate unrecorded public guesses.

### Narrative

The page follows this sequence:

1. **Plain-language answer** — lead with the evidence-supported conclusion, including a mixed or inconclusive outcome if necessary.
2. **At a glance** — recipe reliability, response quality, blind preference, and efficiency remain separate rather than collapsing into one winner score.
3. **Reliability** — completion, JSON/schema validity, and full-response pass overall and across reporting slices.
4. **Quality** — underlying-answer quality, metaphorical coherence, recipe-style execution, and the stricter joint pass.
5. **Blind preference** — prompted wins, fine-tuned wins, ties, and unresolved outcomes without hiding ties.
6. **Efficiency** — input tokens, output tokens, measured latency, adapter size, training time, and compute cost, with recurring and up-front costs distinguished.
7. **Representative responses** — successes, failures, ties, and surprising cases selected transparently and optionally revealed in a Tasting Room-like comparison.
8. **Failure analysis** — where structure, substance, metaphor, execution, similarity, or generalisation failed.
9. **Product decision** — which system powers the Spirit Guide and why.
10. **Boundaries and next steps** — what the results establish, what they do not, and where visitors can continue.

### Interaction

The page is a guided evidence story rather than a live analytics dashboard. Visitors may switch between overall and target-use, cross-domain, or robustness slices. Charts include underlying counts, uncertainty, accessible tables, and direct explanations. The result version and date remain visible.

The exact conclusion, examples, charts, and product decision remain deferred until the formal evaluation is complete.

### Flow

`headline answer → reliability → quality → preference → efficiency → examples → failures → product decision → limitations`

## Agreed initial exclusions

The initial public experience does not require:

- user accounts;
- stored conversation history;
- multi-turn chat;
- public ratings or thumbs controls;
- aggregated Tasting Room voting;
- a public guessing leaderboard;
- public comments;
- live public-result updates; or
- an introductory marketing page in front of the Spirit Guide.

## Deferred design and implementation decisions

Later work must determine:

- visual identity, typography, colour, motion, and illustration;
- final page and control copy;
- exact prompt suggestions and Free Pour starter instructions;
- maximum public input and instruction lengths;
- serving retry and malformed-output policy outside Free Pour;
- validated streaming feasibility;
- mobile comparison details and accessibility testing;
- operational logging, privacy notice, retention, and moderation requirements;
- hosting-specific cold-start and cancellation behaviour;
- whether request-level token or latency details appear publicly;
- whether and how the exact five-shot baseline is exposed in Free Pour;
- the selected Spirit Guide system;
- evidence-dependent Lab detail; and
- all Results content and visualisations.

## Technical approach

The public frontend will use:

- Next.js with the App Router;
- TypeScript;
- Tailwind CSS v4;
- ESLint; and
- the framework's standard local development tooling.

The initial frontend will not add a component library, external state-management library, or animation library. Bespoke semantic components and Tailwind utilities will implement the typographic system. Global CSS remains appropriate for the font face, theme tokens, base document rules, selection and focus behaviour, and genuinely global typography.

The planned application structure separates page routes, shared components, typed fixtures, and response types under a dedicated `frontend/` directory. Neue Montreal Mono will be loaded from an appropriately licensed local webfont asset when available; the implementation may temporarily use a metrics-conscious monospace fallback without downloading or redistributing the commercial font.

### Prototype boundary

The first implementation slice is frontend-only and uses typed mock responses. It includes:

1. the Next.js and Tailwind scaffold;
2. concrete and steel theme tokens;
3. the font hook and global typographic rules;
4. the global header and responsive menu;
5. the Spirit Guide empty state;
6. a mocked mixing transition;
7. a mocked recipe response; and
8. desktop and mobile behaviour.

This slice exists to judge real typography, density, rhythm, interaction, and responsive behaviour before building additional pages or connecting model inference.

### Serving boundary

Python model inference will later sit behind a thin FastAPI boundary rather than being reimplemented inside Next.js. The initial deployment target is a static Next.js export served alongside FastAPI from one Hugging Face Docker Space and one public origin.

If the product later develops a demonstrated requirement for Next.js server-only features, the architecture may introduce a Next.js server and Python inference service behind one reverse proxy. That additional runtime is not part of the initial design.

## Next design step

Build the frontend-only Spirit Guide prototype described above and use it to refine the visual system in the browser. Implementation should preserve the interaction contracts in this document while remaining open to evidence-driven changes in The Lab and Results.

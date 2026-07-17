# ChatG&T Public Experience Decision Log

This log records decisions specific to the eventual public web experience. It is separate from the main experimental decision log so frontend design work can proceed without interfering with active dataset, training, and evaluation work.

## PX-001 — Adopt five public experience areas

- **Date:** 2026-07-16
- **Status:** Agreed

### Decision

The public experience will contain five principal areas:

1. Spirit Guide;
2. Tasting Room;
3. Free Pour;
4. The Lab; and
5. Results.

The Spirit Guide is the homepage. A persistent global menu exposes the five areas, with a conventional compact desktop navigation and recognisable mobile menu.

### Rationale

The structure separates using ChatG&T, playing with the prompting-versus-fine-tuning comparison, and understanding the experiment. Making the Spirit Guide the homepage lets visitors experience the idea before encountering the research explanation.

### Implications

- No separate marketing splash page is required.
- The Lab explains method; Results explains outcome.
- Contextual calls to action connect pages without replacing global navigation.
- Results is not presented as a substantive public destination before formal evidence exists.

## PX-002 — Keep the Spirit Guide single-turn and recipe-led

- **Date:** 2026-07-16
- **Status:** Agreed

### Decision

The Spirit Guide will accept one low-stakes user prompt and render the selected production system's JSON response as a cocktail recipe. It will not initially behave as a multi-turn chat application or collect user feedback.

### Rationale

The interaction matches the behavioural and evaluation population boundaries, keeps the novelty legible, and avoids implying general-purpose assistant coverage. A recipe presentation differentiates the experience from a generic chatbot and makes the response contract visible without exposing raw JSON.

### Implications

- Suggested prompts populate an editable composer.
- The working submit action is **Mix it**.
- Visitors may mix another answer or adjust the existing order.
- Accounts, permanent conversation history, ratings, and follow-up chat are excluded from the initial experience.
- Cold starts and failures are communicated honestly.

## PX-003 — Replace public preference capture with an unrecorded fine-tune guess

- **Date:** 2026-07-16
- **Status:** Agreed; supersedes the earlier Stage 8 public vote-capture intention

### Decision

The Tasting Room will show randomly ordered, identity-concealed responses from System B and System C for the same visitor prompt. The visitor guesses Sample A, Sample B, or Can't tell in response to **Which sample was fine-tuned?** Identities are revealed only after the guess.

The application will not persist or aggregate guesses, and public guesses will not form research evidence, select a system, or alter the controlled evaluation conclusion.

### Rationale

Guessing preserves the participatory nature of the Tasting Room while better serving the educational story of the project. Persisted public voting would introduce storage, privacy, abuse, duplicate-submission, and interpretation work for self-selected observational evidence that cannot replace the frozen held-out evaluation.

### Implications

- The Tasting Room asks about identification, not simultaneous preference.
- Can't tell remains a valid outcome.
- Both samples use identical presentation and are withheld until both are ready.
- Timing, token, and identity clues remain hidden until reveal.
- A failed pair does not expose the successful response or the identity of the failed system.
- The project plan's older “capture votes” wording is historically superseded and should be reconciled when the main planning thread is next updated.
- Operational logging and privacy behaviour still require a deployment decision; unrecorded guessing does not imply the absence of infrastructure logs.

## PX-004 — Add Free Pour as an exploratory prompting experience

- **Date:** 2026-07-16
- **Status:** Agreed

### Decision

Free Pour will let a visitor write system-level instructions for the base model and compare its response with the fine-tuned model's response to the same user prompt.

The first run produces **Your Pour** from the base model plus visitor instructions and **House Pour** from the fine-tuned model without detailed ChatG&T instructions. During refinement, the House Pour remains fixed while the visitor edits instructions and regenerates only Your Pour.

### Rationale

Free Pour makes the difference between prompting and learned behaviour tangible. A fixed House Pour creates a stable comparison, reduces serving cost, and helps visitors see the effect of their instruction changes.

### Implications

- Free Pour is visibly exploratory and not part of the formal experiment.
- Visitor instructions are labelled in ordinary language rather than requiring knowledge of the term “system prompt.”
- Empty instructions, a short editable head start, and the frozen experimental baseline are planned starting options.
- Instruction or input-token length is made visible where feasible.
- Non-schema output is shown safely as **Unmixed output**, not silently repaired.
- Iteration history may exist within the browser session but is not permanent account history.

## PX-005 — Separate method, evidence, and public participation

- **Date:** 2026-07-16
- **Status:** Agreed

### Decision

The Lab will explain the research question, systems, response contract, training process, evaluation, measurements, and limitations. Results will separately present the frozen conclusion, reliability, quality, blind preference, efficiency, representative examples, failures, product decision, and boundaries.

Public Spirit Guide, Tasting Room, and Free Pour interactions remain demonstrations rather than additions to the formal evaluation dataset.

### Rationale

Separating method from outcome gives each page a clear purpose and allows the project to present positive, negative, mixed, or inconclusive results honestly. Keeping public interactions outside the frozen evidence protects the interpretation of the controlled experiment.

### Implications

- Detailed Lab content remains adaptable until the main work is complete.
- Results does not collapse multiple objectives into a single winner score.
- Ties, uncertainty, structural failures, and quality failures remain visible.
- The selected Spirit Guide system and rationale are explained only after evidence supports the decision.
- Public guesses do not appear in Results.

## PX-006 — Use one shared, accessible interaction language

- **Date:** 2026-07-16
- **Status:** Agreed

### Decision

All interactive pages will reuse the same accessible recipe presentation and maintain clear user-prompt scope, honest waiting states, equivalent comparison styling, and recoverable failures. Cocktail language may provide personality but may not obscure actual system state or response content.

### Rationale

Shared components make comparisons fair and the product coherent. Honest operational language is especially important because the expected deployment may include model cold starts and constrained infrastructure.

### Implications

- Partial raw JSON is not exposed as a normal response.
- The application does not simulate precise progress it cannot measure.
- Comparison pages do not reveal identity through unequal styling or progress.
- Core content and controls remain usable without animation.
- Exact retry, privacy, retention, accessibility, and hosting behaviour remain implementation decisions to settle before deployment.

## PX-007 — Adopt a typography-only concrete and steel visual system

- **Date:** 2026-07-16
- **Status:** Agreed

### Decision

The public experience will use Neue Montreal Mono as its typeface, subject to appropriate web licensing. Typography, spacing, rules, visible grids, flat colour fields, glyphs, and typographic motion will form the complete visual identity.

The initial palette avoids pure black and pure white. It uses warm concrete and cool steel neutrals, beginning with `#D7D5CD`, `#B8B6AF`, `#555C5E`, and `#292F30`. The mid-steel value replaces the initial `#687072` after browser validation established approximately 4.64:1 rather than 3.44:1 contrast for small metadata against concrete-light. Normal concrete/steel and inverted steel/concrete fields provide the primary emphasis mechanism.

The initial direction has no accent colour. One may be added later only for a demonstrated functional or accessibility need.

### Rationale

Neue Montreal Mono already provides a strong technical and expressive vocabulary through its weights, fixed-width rhythm, numerals, punctuation, coding ligatures, and boxed glyph treatments. A disciplined single-typeface system better expresses experimental brutalist mixology than a separate layer of cocktail imagery or simulated materials.

Concrete and steel describe the palette and structural attitude rather than literal surfaces. Avoiding absolute black and white keeps the interface industrial and mineral without producing generic stark technology branding.

### Implications

- The initial experience uses no photography, illustration, decorative imagery, separate icon set, textures, shadows, ornamental three-dimensional assets, or simulated glass and concrete effects.
- Glass is not a visual motif.
- Cocktail character comes from measurements, labels, content, and interaction language.
- Brutalism comes from direct structure without compromising usability.
- Words and typeface glyphs replace icons where they remain clear and accessible.
- Monospaced body text uses controlled line lengths and generous leading.
- Colour values, type sizing, weight assignments, and motion details must be validated in rendered layouts.
- Reduced-motion behaviour and accessible contrast are required.

## PX-008 — Build the public frontend with Next.js and Tailwind CSS

- **Date:** 2026-07-16
- **Status:** Agreed

### Decision

Build the public frontend with Next.js App Router, TypeScript, Tailwind CSS v4, and ESLint under a dedicated `frontend/` directory.

The first implementation slice will be frontend-only and use typed mock responses. It will establish the concrete and steel theme, font hook, global navigation, Spirit Guide empty state, mocked mixing transition, mocked recipe response, and responsive behaviour before any model-serving integration.

Python inference will later be exposed through a thin FastAPI boundary. The initial deployment design uses a static Next.js export served alongside FastAPI from one Hugging Face Docker Space and one public origin.

### Rationale

A running browser prototype will reveal the typography, scale, spacing, rhythm, state changes, and responsive behaviour more directly than detached wireframes. Next.js provides the agreed page structure and React interaction model, while Tailwind CSS supports rapid composition of the bespoke type-led system.

Keeping model inference in Python preserves the existing project boundary. A static-first frontend avoids introducing a second production application server before the product demonstrates a need for Next.js server-only features.

### Implications

- The initial frontend has no component library, external state-management library, or animation library.
- Tailwind utilities implement component styling; global CSS holds font loading, theme tokens, base document rules, focus and selection behaviour, and genuinely global typography.
- Neue Montreal Mono requires an appropriately licensed local webfont asset before public deployment and will not be downloaded or redistributed implicitly.
- Typed fixtures let the design proceed without loading or querying the model.
- The frontend does not initially use Next.js route handlers, server actions, or other features incompatible with static export.
- A Next.js server and reverse proxy may be added only for a demonstrated server-side requirement.
- Real inference endpoints, request limits, retries, concurrency, cold-start behaviour, and deployment privacy remain later implementation decisions.

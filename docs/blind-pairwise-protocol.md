# Blinded Pairwise Protocol

**Primary comparison:** System B (five-shot base) versus System C (minimal-prompt fine-tune)
**Status:** Frozen

Pairwise preference answers a different question from schema validity and dimensional scoring: when both strategies produce contract-valid responses, which complete answer is preferred?

## Frozen presentation order

Before any responses exist, the 60 held-out prompt IDs are assigned a pair-order label from seed `20260715`: exactly 30 display B first and 30 display C first. This schedule is stored and hashed with the held-out set.

Eligibility is learned later. Only prompts where both B and C are schema-valid receive a conditional pairwise judgment, so the eligible subset may not retain a 30/30 order balance. The achieved order counts are reported; order is never re-randomised around the observed validity results.

## Judge packet

For each eligible prompt, a judge sees:

- the exact user prompt;
- two responses rendered through the same field order, labels, typography, and whitespace treatment;
- opaque labels `Response A` and `Response B`; and
- the frozen question: "Which response better fulfils the prompt while sustaining a coherent and natural cocktail-recipe response?"

Renderer `chatgnt-pairwise-json-v1` uses parsed schema-valid content with top-level order `title`, `ingredients`, `method`, `garnish`; ingredient order `amount`, `unit`, `name`; UTF-8 unescaped; two-space indentation; LF; and one final newline. It does not rewrite words or hide content. The exact packet template is fixed in `config/judge-manifest-v1.json`; judgments bind manifest, packet, renderer, and order-schedule identities.

Allowed choices are `response_a`, `response_b`, and `tie`. A tie means neither response is meaningfully preferable overall; it is not a substitute for uncertainty. A judge who genuinely cannot assess returns `unable_to_assess`, triggering one second blinded judgment under the same resolution and denominator rules as qualitative judging. If it remains unresolved, the pair is reported as unresolved and excluded from conditional preference denominators while remaining visible in the eligible-pair count.

## Conditional and end-to-end outcomes

The conditional result uses only mutually schema-valid, resolved pairs. After identity reveal, it reports B wins, C wins, and ties as separate counts and rates. Preference among decisive comparisons is supplementary and never replaces the three-way result.

The end-to-end outcome exists for all 60 prompts:

- both valid: use the resolved blind choice;
- only B valid: B wins;
- only C valid: C wins;
- neither valid: `both_failed`;
- both valid but judgment remains unresolved: `unresolved`.

These outcomes are reported separately because automatic wins for validity answer a broader engineering-strategy question than conditional human/LLM preference.

## Judge roles and calibration

One primary LLM judge assesses every eligible pair in a fresh blinded context. Human calibration targets **15 eligible pairs**. Within each slice select the five lowest SHA-256 ranks of `human-pair-calibration-v1|20260715|prompt_id`; fill a total shortfall from all remaining eligible pairs in the same global hash order. If fewer than 15 are eligible, select all. The executable selector and fixed-vector tests are authoritative.

Fifteen is a pragmatic calibration sample, not a powered preference study. It gives each target-use, cross-domain, and robustness slice five opportunities for human–LLM comparison without asking the project author to judge every pair. The human and LLM choice rates are reported separately. Exact choice agreement and tie/disagreement counts are reported with their paired denominator; no agreement threshold is treated as proof of judge validity.

Human calibration selection occurs before LLM pairwise choices are revealed. Judges must not evaluate a pair they authored if a separate reviewer is practical; any overlap in roles is disclosed.

Every pair packet is re-rendered from the exact two schema-valid outputs and checked against the canonical 60-prompt B/C order schedule. Packet IDs bind prompt plus ordered response IDs. The aggregate gate requires exactly one primary judgment for every eligible pair and exactly the deterministic 15-prompt human sample, with no missing, duplicate, or orphan records. Unable-to-assess resolution uses the same fresh-context, different-judge, identical-packet chain as qualitative scoring.

## Reveal and integrity

Judgment packets, response-order mapping, LLM judgments, and human judgments are separate files. Packets and completed judgments are hashed before mapping opens. Each record carries protocol, judge-manifest, packet, renderer and schedule identities plus judge session, choice, rationale, and resolution status.

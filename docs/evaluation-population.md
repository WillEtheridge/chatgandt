# Evaluation Population

This document defines the conceptual population of user prompts to which the ChatG&T experiment is intended to apply and records the frozen blueprint for the held-out sample. The exact prompts will be authored only after the training and validation data are frozen and before any fine-tuning begins.

## Target-population statement

> The target evaluation population consists of English-language, single-turn, low-stakes prompts that can be answered concisely using stable general knowledge. Prompts may seek advice, decision support, explanation, emotional support, short-form transformation, or creative generation, and may be expressed as questions, requests, commands, statements, or fragments.

A suitable prompt must be answerable without external tools or live information, and its answer must fit naturally within ChatG&T’s concise recipe structure.

## Intent families

### 1. Advice and decision support

Low-stakes prompts about areas such as careers, relationships, communication, productivity, everyday choices, general budgeting, and travel preparation.

### 2. Explanation and technical understanding

Prompts asking for explanations of stable general knowledge, concepts, technology, science, or small technical problems.

### 3. Low-stakes emotional support

Prompts about ordinary experiences such as feeling overwhelmed, loneliness, confidence, motivation, or handling setbacks.

### 4. Creative generation

Prompts asking for concise creative outputs such as premises, names, ideas, characters, or themes.

### 5. Short-form transformation

Prompts asking for a short piece of content to be rewritten, clarified, summarised, or otherwise transformed, including small concrete artefacts.

Unusual hypotheticals may appear across these intent families to test whether the ChatG&T behaviour transfers beyond familiar scenarios.

## Reporting slices

Results will be reported separately for three evaluation slices:

| Slice | Purpose |
| --- | --- |
| Target-use prompts | Measure ordinary performance on intended tasks |
| Cross-domain prompts | Test whether the learned behaviour transfers to topics withheld from training |
| Robustness prompts | Test JSON generation, format persistence, multiple constraints, and resistance to instructions that attempt to break the target behaviour |

Robustness prompts should contain a legitimate underlying task so that format persistence and answer usefulness can both be evaluated.

## Exclusions

The target evaluation population excludes:

- professional, emergency, or crisis guidance;
- requests dependent on current news or live information;
- tasks requiring browsing, external tools, or private data;
- long documents or large context windows;
- long-form essays, applications, or substantial code generation;
- obscure trivia intended primarily to test factual recall;
- multi-turn conversations; and
- non-English prompts.

Small quoted passages and short code fragments remain in scope because they create relevant structured-generation and JSON-escaping challenges.

## Held-out sample size

The held-out evaluation will contain **60 prompts**.

This is a pragmatic portfolio-scale sample rather than a statistically powered benchmark. It is large enough to provide 12 prompts per intent family if those families are balanced equally, expose recurring failures across varied inputs, and produce a more stable overall comparison than the previously considered 40-prompt minimum. It remains manageable across four systems: a complete evaluation would generate 240 responses and 60 primary B-versus-C pairwise comparisons.

Near a 50% outcome, 60 independent observations have a rough 95% margin of error of about 13 percentage points. The evaluation can therefore identify large differences, recurring patterns, and efficiency trade-offs, but it cannot establish small performance improvements precisely. Overall rates will be reported with uncertainty intervals. Intent-family and reporting-slice results will be treated as diagnostic rather than conclusive because their sample sizes are smaller.

Pairwise results will retain fine-tuned wins, prompted-baseline wins, and ties as separate outcomes. Any preference rate calculated only over decisive comparisons will be reported as supplementary context rather than replacing the raw three-way result.

## Held-out allocation

The five intent families will be represented equally, with 12 prompts each. Within every family, six prompts will represent ordinary target use, three will test cross-domain generalisation, and three will test robustness.

| Intent family | Target use | Cross-domain | Robustness | Total |
| --- | ---: | ---: | ---: | ---: |
| Advice and decision support | 6 | 3 | 3 | 12 |
| Explanation and technical understanding | 6 | 3 | 3 | 12 |
| Low-stakes emotional support | 6 | 3 | 3 | 12 |
| Creative generation | 6 | 3 | 3 | 12 |
| Short-form transformation | 6 | 3 | 3 | 12 |
| **Total** | **30** | **15** | **15** | **60** |

Equal intent-family representation prevents the aggregate result from being dominated by a category that happens to favour one system. The reporting slices are deliberately not equal: target-use prompts form half of the sample because ordinary intended use is the main evaluation target, while cross-domain and robustness prompts provide substantial but secondary stress tests.

## Input-form coverage

Prompts will be classified by their communicative function rather than punctuation.

| Input form | Count | Operational meaning |
| --- | ---: | --- |
| Question | 15 | Primarily asks for information, explanation, or advice |
| Direct request or command | 30 | Primarily asks the system to perform a task; this includes question-shaped requests such as “Can you rewrite this?” |
| Statement or fragment | 15 | Presents a situation or need conversationally without a complete direct request |

The forms need not be distributed equally within every intent family. Explanations may naturally contain more questions, creative and transformation tasks more requests, and emotional-support prompts more statements. The global quota preserves meaningful variety without forcing unnatural phrasing into individual families.

## Task complexity and ordinary constraints

Difficulty will not be assigned as a subjective easy/medium/hard label. Instead, prompts will use two observable task-complexity categories:

| Complexity | Count | Operational meaning |
| --- | ---: | --- |
| Standard | 40 | One clear underlying task, little necessary context, and no explicit constraint beyond the task itself |
| Composed | 20 | Includes at least one concrete source of additional complexity, such as multiple outcomes, a meaningful constraint, supplied material, competing considerations, or several connected steps |

Ten of the composed prompts will contain an explicit, legitimate user constraint, with two in each intent family. Examples include a requested count, length, audience, tone, inclusion, or exclusion. These are ordinary task requirements rather than attempts to break the ChatG&T behaviour. The other ten composed prompts may derive their complexity from context, supplied material, multiple outcomes, competing considerations, or connected steps without an explicit constraint.

## Robustness roles

The 15 robustness prompts will be divided equally across three focused roles:

| Robustness role | Count | What it tests |
| --- | ---: | --- |
| Format pressure | 5 | An explicit request for Markdown, prose, XML, or another output shape instead of the required JSON |
| Behaviour pressure | 5 | An instruction to abandon the cocktail concept, ignore prior instructions, or answer normally |
| Serialization pressure | 5 | Quotes, line breaks, code, or other supplied content that makes valid JSON harder to produce |

Each intent family will contain one prompt from each robustness role. Every robustness prompt must retain a legitimate underlying task so that behaviour persistence and answer usefulness remain jointly assessable. These are focused contract-persistence tests, not claims of comprehensive security or jailbreak evaluation.

## How the quotas combine

These classifications describe the same 60 prompts from different angles; they are not separate sets whose totals should be added together. For example, one prompt may simultaneously be labelled `emotional_support`, `target_use`, `statement_or_fragment`, `composed`, and `constraint_bearing`.

## Deferred decisions

The following will be determined during the remainder of the evaluation-design stage:

- the topics deliberately withheld from training;
- the later prompt-authoring, collision-review, and replacement-log procedure; and
- the operational test for whether a prompt is sufficiently unseen.

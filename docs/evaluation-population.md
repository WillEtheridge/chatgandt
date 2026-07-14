# Evaluation Population

This document defines the conceptual population of user prompts to which the ChatG&T experiment is intended to apply. It does not define the size or composition of the eventual held-out test sample.

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

## Deferred decisions

The following will be determined during the evaluation-design stage:

- the number of held-out prompts;
- quotas for intent families, input forms, and reporting slices;
- the topics deliberately withheld from training;
- the prompt-authoring and review procedure; and
- the operational test for whether a prompt is sufficiently unseen.

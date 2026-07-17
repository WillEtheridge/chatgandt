# Dataset v1 Design

- **Stage:** 4 — Build and freeze dataset v1
- **Status:** Dataset contract, split procedure, and authoring guide implemented; candidate authoring pending
- **Date:** 2026-07-15

This document records the source-of-truth design for ChatG&T's supervised dataset before exact records or split assignments are created. Exact held-out prompts do not yet exist and are outside Stage 4.

## Canonical unit of data

One supervised example is one independent, single-turn user input paired with one ideal ChatG&T response.

The canonical dataset stores semantic source data rather than model-ready chat messages. Its core shape is:

```json
{
  "example_id": "example-001",
  "scenario_id": "interview-preparation",
  "user_prompt": "Help me prepare for an interview.",
  "assistant_response": {
    "title": "The Confident Candidate",
    "ingredients": [],
    "method": [],
    "garnish": "..."
  },
  "metadata": {}
}
```

The exact metadata schema is defined by `supervised-example-v1`. It retains stable identities, coverage labels, provenance, and eventual split information, while review history remains in separate workflow events.

The assistant response is stored as a JSON object and must pass the frozen ChatG&T response schema. This avoids double-encoded JSON during authoring and keeps authored meaning separate from model-specific rendering.

## Canonical record architecture

The complete source record has this shape:

```json
{
  "record_schema_version": 1,
  "example_id": "dataset-v1-001",
  "scenario_id": "scenario-career-interview-preparation",
  "user_prompt": "Help me prepare for a job interview.",
  "assistant_response": {
    "title": "The Confident Candidate",
    "ingredients": [
      {"amount": 50, "unit": "ml", "name": "role-specific preparation"},
      {"amount": 30, "unit": "ml", "name": "evidence from past experience"},
      {"amount": 2, "unit": "dashes", "name": "calm curiosity"}
    ],
    "method": [
      "Research the role and identify the abilities the interviewer is likely to explore.",
      "Prepare three concise examples showing the situation, your actions, and the result.",
      "Practise aloud, then prepare one thoughtful question about the team."
    ],
    "garnish": "A clear explanation of why this particular role suits you."
  },
  "metadata": {
    "intent_family": "advice_decision_support",
    "coverage_slice": "target_use",
    "input_form": "direct_request_or_command",
    "complexity": "standard",
    "complexity_sources": [],
    "constraint_bearing": false,
    "robustness_role": null,
    "topic": "career_and_work",
    "task_subtype": "preparation",
    "user_goal": "prepare effectively for a job interview",
    "requested_task_or_artefact": "an actionable preparation plan",
    "scenario_summary": "A person wants general help preparing for an upcoming job interview.",
    "important_constraints": []
  },
  "provenance": {
    "authoring_batch_id": "dataset-v1-batch-01",
    "initial_draft_source": "frontier_model",
    "initial_draft_model_id": "recorded-model-identity",
    "model_revision_used": false,
    "material_human_edit": false
  },
  "split": null,
  "pilot_member": false
}
```

`assistant_response` references the existing frozen response schema rather than redefining it. `split` is null during authoring and becomes `train` or `validation` during final assignment. A frozen accepted record may not retain a null split, and only a training record may have `pilot_member` set to true.

The record deliberately reuses the held-out protocol's descriptive vocabulary where the concepts are the same. `topic`, `user_goal`, `requested_task_or_artefact`, `scenario_summary`, and `important_constraints` also provide the metadata view used by later contamination retrieval. `coverage_slice` and `task_subtype` are dataset-specific additions.

Intent family, coverage slice, input form, complexity source, robustness role, draft source, and split use closed enums. Topic and task subtype use versioned controlled registries so spelling variants cannot create false categories. User goal, requested task or artefact, scenario summary, and individual constraint descriptions remain non-empty explanatory text.

Cross-field validation will enforce at least these invariants:

- robustness records are composed, carry one robustness role, and include `robustness_pressure` among their complexity sources;
- non-robustness records have a null robustness role;
- standard records have no complexity sources, no compatible constraint, and no important constraints;
- constraint-bearing records are composed, include `ordinary_content_constraint`, and describe at least one important constraint;
- non-constraint-bearing records do not claim `ordinary_content_constraint` and have no important constraints;
- every frozen record has an assigned split;
- pilot members belong to training; and
- every example sharing a scenario ID belongs to the same split.

Some metadata is intentionally redundant: for example, `constraint_bearing` is recoverable from `important_constraints`. Keeping the explicit label makes records and reports easier to inspect, while the cross-field validator prevents disagreement.

## Derived training representation

A deterministic preparation step converts each accepted source record into:

1. an explicit system message with empty content;
2. the exact user prompt as the user message; and
3. a canonical JSON serialization of `assistant_response` as the assistant message.

The official pinned Qwen chat template is applied only when preparing model input. Rendered messages or token sequences are reproducible derived artefacts, not the authored source of truth. Five-shot examples are never inserted into supervised training messages.

## Authoring and provenance policy

Dataset v1 will be model-assisted synthetic data with explicit project-author responsibility.

- The project author and Codex agree the blueprint and authoring guide.
- A frontier model may draft or revise examples in small, reviewable batches.
- Automated checks reject structurally invalid records.
- A separate review pass checks usefulness, metaphorical coherence, recipe-style execution, variety, and compliance with the authoring guide.
- The project author inspects representative samples plus difficult, disputed, or high-risk records.
- Per-example provenance distinguishes model drafting, model revision, and material human editing.
- Final inclusion is a project decision; model generation alone never makes an example accepted.

The dataset will be described honestly as original project-authored, model-assisted synthetic supervision. It will not be described as 150–300 examples written entirely by hand.

Qwen outputs will not be used as target responses or as evidence for selecting, rewriting, or rejecting examples. This avoids teaching the target model its existing habits or tuning supervision around observed target-model failures.

The canonical record retains only a compact provenance summary: authoring batch, initial draft source, initial model identity when applicable, whether a model revision was used, and whether a human made a material edit. Initial draft source is either `human` or `frontier_model`; a human-authored draft has a null initial model identity.

Detailed process history is stored separately as append-only workflow records keyed by example ID. The workflow distinguishes `draft_created`, `model_revision`, `human_edit`, `quality_review`, `accepted`, and `rejected` events and records the actor, time, outcome, reason codes, and notes appropriate to the event. The frozen Step 7 authoring guide maps the three quality dimensions to `pass`, `revision_requested`, or `rejection_recommended` and gives concrete use guidance for every reason code.

Review state and rejection history do not become part of the text used for training. This keeps the semantic source record readable and model-independent while retaining an auditable account of how it entered or left the accepted set.

## Permitted and restricted authoring inputs

Authors may inspect:

- the frozen behavioural contract and response schema;
- the frozen safety policy;
- the Stage 4 coverage blueprint and authoring guide once agreed;
- the frozen high-level evaluation population and withheld-topic policy; and
- dataset records already created in Stage 4 for consistency and duplication review.

The following may not be used as drafting seeds, templates, or paraphrase sources:

- the five-shot user/response examples;
- prompt-development scenarios;
- development outputs;
- any later held-out prompt candidate; and
- any output generated by the target base or adapted model.

The project author has prior knowledge of existing development material, so the project will not claim impossible blindness. Instead, exact, lexical, semantic, metadata, and human-readable checks will test that retained examples do not copy or superficially disguise those materials.

Photography, tabletop games, and pottery/ceramics remain substantively excluded from both training and validation under the frozen withheld-topic policy.

## Scenario identity and split isolation

Two examples belong to the same scenario group when all three statements are true:

1. they have substantially the same user goal;
2. they involve substantially the same situation, concept, source material, or requested artefact; and
3. the substantive answer could be reused after changing only surface details.

Shared intent, task form, domain, or response structure does not by itself make two examples the same scenario. Superficial substitutions inside an otherwise reusable prompt and answer do.

Every candidate receives a `scenario_id` before final split assignment. All records with the same scenario ID remain in one split. When grouping is genuinely uncertain, the conservative default is to keep the records together.

Training and validation assignment operates on scenario groups rather than individual examples. This protects validation from near-duplicate recall while still allowing it to measure transfer across examples that share a broad capability.

## Dataset size, split targets, and pilot

Dataset v1 targets exactly 200 accepted examples. Authoring may produce approximately 220–240 candidates so structurally weak, qualitatively weak, duplicative, excluded-topic, or otherwise unsuitable records can be rejected without lowering the accepted target. The candidate range is a planning estimate rather than permission to retain filler, and rejection reasons remain recorded.

The accepted-set allocation targets:

- 160 training examples;
- 40 validation examples; and
- a fixed 40-example pilot subset drawn only from the training split.

Scenario isolation takes precedence over the exact 160/40 arithmetic. Whole scenario groups remain in one split even when this produces a small count deviation. The achieved split sizes and reasons for any deviation will be reported.

Across the five frozen intent families, the initial targets are:

| Set | Total | Target per intent family |
| --- | ---: | ---: |
| Full accepted dataset | 200 | 40 |
| Training split | 160 | 32 |
| Validation split | 40 | 8 |
| Training-only pilot | 40 | 8 |

Intent-family balance is a primary coverage target, but it cannot justify breaking scenario groups. Input form, task type, complexity, constraints, tone, and other later coverage dimensions cross these family totals rather than creating separate additive quotas.

Validation supports loss monitoring, obvious overfitting diagnosis, qualitative transfer inspection, and selection among a small number of justified training configurations. It is not held-out evidence and will not be presented as the final research result.

The pilot is a representative pipeline diagnostic, not another split. It will cover all five intent families and varied input forms, complexity, and constraints. It is fixed after the training split is assigned and before any training begins. Pilot outputs may inform training mechanics but cannot be used to rewrite or replace supervised examples around Qwen's behaviour.

Example count is not the complete training budget. Before freeze, the project will report user-prompt tokens, assistant-response tokens, total supervised tokens, token distributions by split and intent family, and every example affected by the planned sequence-length limit. A count-balanced dataset with a severely imbalanced token distribution is not considered balanced.

## Coverage blueprint

Coverage is planned with a small set of cross-cutting targets. These labels describe different properties of the same example; their totals are not additive dataset partitions.

Each of the five intent families contributes 40 accepted examples:

1. advice and decision support;
2. explanation and technical understanding;
3. low-stakes emotional support;
4. creative generation; and
5. short-form transformation.

Within every intent family, the targets are:

| Coverage dimension | Per family | Dataset total |
| --- | ---: | ---: |
| Target-use examples | 28 | 140 |
| Breadth examples | 6 | 30 |
| Robustness examples | 6 | 30 |
| Questions | 10 | 50 |
| Direct requests or commands | 20 | 100 |
| Statements or fragments | 10 | 50 |
| Standard-complexity examples | 24 | 120 |
| Composed-complexity examples | 16 | 80 |
| Compatible explicit constraints | 12 | 60 |

`Target-use` covers the ordinary, low-stakes behaviour the portfolio experience is intended to serve. `Breadth` deliberately stretches topic or task variety without entering a frozen withheld domain. `Robustness` applies pressure to behavioural persistence or exact output validity while still requiring a useful answer.

The 30 robustness examples are all composed-complexity examples. Within each intent family they contain two `format_pressure`, two `behaviour_pressure`, and two `serialization_pressure` examples, producing 10 of each role overall. Robustness pressure does not itself count toward the 60 compatible explicit constraints. A compatible constraint is an ordinary requirement the answer should fulfil, such as providing three options, writing for a beginner, preserving a supplied phrase, or including a concrete next step.

Composed complexity means that success requires the model to satisfy the ordinary ChatG&T behaviour while also handling at least one additional observable demand, such as an explicit constraint, supplied material, or robustness pressure. The 80-example target deliberately gives substantial supervision to joint behaviour rather than allowing the dataset to consist mostly of easy format demonstrations.

### Topic and task diversity

The accepted dataset targets:

- at least 12 substantive domains overall;
- at least eight substantive domains within each intent family;
- no single topic above 10% of the full dataset;
- at least six task subtypes within each intent family; and
- no single task subtype above 25% of its intent family.

The original brief's example categories may seed domain vocabulary, but they are not separate quotas. Photography, tabletop games, and pottery/ceramics remain prohibited rather than counting as breadth.

Every record receives one primary topic: the context most necessary to answering the prompt, rather than every subject it happens to mention. The version 1 topic registry is:

1. `career_and_work`;
2. `learning_and_study`;
3. `technology_and_software`;
4. `science_and_mathematics`;
5. `history_and_society`;
6. `money_and_budgeting`;
7. `relationships_and_social_life`;
8. `personal_growth_and_wellbeing`;
9. `habits_and_productivity`;
10. `home_and_everyday_life`;
11. `travel_and_places`;
12. `food_and_cooking`;
13. `arts_and_culture`;
14. `writing_and_communication`;
15. `business_and_marketing`;
16. `community_and_events`;
17. `consumer_choices`;
18. `nature_and_environment`;
19. `leisure_and_entertainment`; and
20. `fictional_and_imaginative_worlds`.

`personal_growth_and_wellbeing` excludes medical diagnosis and treatment. `money_and_budgeting` covers low-stakes personal finance rather than personalised investment, tax, or debt-crisis advice. The three withheld domains remain prohibited even when they could be placed under a broader permitted topic. There is no `other` value: a genuinely missing domain requires an explicit registry revision before dataset freeze.

Every record also receives one primary task subtype from the registry belonging to its intent family. Topic describes subject matter; task subtype describes the operation the user wants.

| Intent family | Permitted task subtypes |
| --- | --- |
| Advice and decision support | `action_planning`, `option_comparison`, `prioritisation`, `preparation`, `habit_change`, `interpersonal_navigation`, `problem_diagnosis`, `risk_and_tradeoff_assessment` |
| Explanation and technical understanding | `concept_explanation`, `process_explanation`, `cause_and_effect`, `comparison_and_distinction`, `worked_example`, `troubleshooting`, `misconception_correction`, `technical_how_to` |
| Low-stakes emotional support | `validation_and_normalisation`, `perspective_reframing`, `self_compassion`, `confidence_support`, `manageable_next_steps`, `conversation_preparation`, `boundary_reflection`, `supporting_someone_else` |
| Creative generation | `name_generation`, `slogan_or_tagline`, `character_or_mascot`, `story_premise_or_plot`, `scene_or_opening`, `concept_or_campaign`, `event_or_experience`, `idea_generation` |
| Short-form transformation | `summarisation`, `clarity_edit`, `tone_shift`, `audience_adaptation`, `notes_to_finished_copy`, `shortening`, `message_or_reply_drafting`, `constraint_preserving_rewrite` |

Topic, intent family, task subtype, coverage slice, and robustness role remain independent. For example, an XML-pressure mascot request may be classified as `community_and_events`, creative generation, `character_or_mascot`, robustness, and `format_pressure`. The robustness mechanism does not replace the underlying task label.

The hard diversity rules remain at least 12 topics overall, at least eight topics per family, no topic above 20 examples, at least six task subtypes per family, and no subtype above 10 of that family's 40 examples. All eight subtypes should appear when they fit naturally, but exact equal allocation is not required.

### Response diversity audit

Response variety is checked as an audit rather than controlled through exact quotas. Review and freeze reports will inspect:

- ingredient counts across the permitted three-to-eight range;
- method length and sentence structure;
- title patterns;
- measurement-unit patterns;
- repeated ingredient metaphors and advice sequences;
- garnish style;
- warm, playful, direct, calm, technical, and imaginative tones; and
- lexical and semantic similarity between responses.

Every permitted ingredient count must appear, and no one count should occupy more than roughly one third of the accepted set. Repeated distinctive templates or phrases trigger review. These are diversity guardrails, not reasons to retain a weaker example merely to satisfy a decorative quota.

### Validation coverage

The validation target remains eight examples per intent family. Across the complete validation split, all three input forms, both complexity levels, target-use, breadth, robustness, compatible constraints, and all three robustness roles must appear. Scenario isolation takes precedence over exact cross-cutting arithmetic, and any material deviation is reported.

## Next action

The dataset contract, allocation procedure, authoring rubric, and batch workflow are now fixed. Stage 4 continues by creating the 10-candidate calibration batch under the authoring guide, without inspecting exact held-out prompts or querying Qwen.

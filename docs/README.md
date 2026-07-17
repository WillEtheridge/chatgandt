# ChatG&T Documentation

This directory records both the experiment and what we learned while building it.

## Start here

- [Project plan](project-plan.md) — current stage, completed work, and next action
- [Experiment plan](experiment-plan.md) — research question and comparison design
- [Decision log](decisions.md) — consequential choices and their rationale
- [Learnings log](learnings.md) — reusable engineering and research lessons
- [Limitations](limitations.md) — validity risks and honest boundaries

## Stage records

- [Stage 2](stage-2/) — model selection, environment, inference harness, schema validation, and prompt development
- [Stage 3](stage-3/) — evaluation-protocol readiness records
- [Stage 4](stage-4/) — dataset design, production, auditing, amendments, and freeze evidence
- [Stage 5](stage-5/) — held-out-set readiness
- [Stage 6](stage-6/) — pilot and full-training preparation
- [Stage 7](stage-7/) — held-out execution, analysis, judge calibration, and primary results
- [Operations](operations/) — reusable infrastructure procedures
- [Product](product/) — public portfolio experience, interface decisions, and deployment evidence

## Live deployment

- [Hugging Face deployment runbook](operations/huggingface-deployment-runbook.md) — reproduce, verify, and operate the private inference path
- [Hugging Face deployment results](product/huggingface-deployment-results.md) — deployed identities, verified properties, and remaining Vercel handoff

## Frozen protocol documents

The protocol documents that remain at the root are intentionally not moved. Their exact paths and bytes are bound by the frozen Stage 3 evaluation manifest. Keeping them stable preserves the existing verification chain while the working records are organised by stage.

These include the behavioural contract, experiment and evaluation definitions, contamination controls, qualitative and pairwise protocols, response-similarity protocol, held-out authoring protocol, and Stage 3 protocol overview.

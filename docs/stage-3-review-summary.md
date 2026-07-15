# Stage 3 Review Summary

- **Protocol:** `chatgnt-evaluation-v1`
- **Review date:** 2026-07-15
- **Outcome:** Accepted for freeze
- **Unresolved experiment-validity blockers:** 0

## What was reviewed

Stage 3 fixes the 60-prompt evaluation blueprint, the four compared systems, structural and qualitative scoring, blind B-versus-C comparison, uncertainty reporting, contamination checks, response-similarity checks, and the later held-out-authoring procedure. It contains no training examples and no exact held-out prompts.

Six fresh LLM review sessions challenged the specification and executable checks. These were separate model contexts, not independent human experts. Findings were tested with deliberately inconsistent fixtures before being accepted as resolved.

## Material improvements from review

The review cycle caused the project to:

- bind the exact A/C minimal prompt and B/D five-shot prompt rather than trusting version labels;
- bind the harness, model, runtime, prompt, and system configuration that define the two-by-two experiment;
- enforce the complete 60-prompt quota matrix and formal 240-attempt system population;
- distinguish prompt contamination from generated-response similarity;
- preserve structural failures in end-to-end denominators;
- define deterministic pair ordering, human-calibration samples, shortfall handling, and uncertainty calculations;
- reject exact project-data collisions and require recorded review for substantive overlap;
- keep training/validation authoring, held-out authoring, training, and held-out generation in the declared order; and
- record the limits of local evidence instead of presenting hashes as external attestation.

The final targeted test substitutes a different but internally consistent five-example prompt for Systems B and D. It is rejected, demonstrating that the selected prompt treatment—not merely the label `five-shot-v3`—is frozen.

## Proportionality decision

The review loop eventually moved from protecting experimental validity toward defending local files against a person who controls the repository. That is not a useful requirement for this portfolio experiment. Stored hashes establish identity and reproducibility; they do not prove execution to an external party. Independent attestation would require an external trust anchor such as protected CI and signed provenance.

Further review was stopped once no unresolved finding could change the compared treatments, evaluation population, scoring rules, denominators, or interpretation of the primary result. Remaining local-trust and detailed chronology concerns are recorded as limitations rather than blockers.

## Verification at acceptance

The accepted review candidate passed:

- 128 repository tests;
- the ordinary evaluation-protocol verifier;
- the real pinned MiniLM semantic verifier with calibration recall@5 of `1.0`;
- the canonical live dry-review gates; and
- the coherent substitute-prompt negative test.

The freeze command reruns the live gates and records the final evidence and identities. It performs only the lifecycle transition; changing a normative evaluation asset requires a new protocol version.

## Boundary check

At acceptance, the repository contained no Stage 4 supervised examples, exact Stage 5 held-out prompts, pilot/full fine-tuning run, or held-out generation. Stage 4 may therefore begin after the status-only freeze.

# Held-out Authoring, Replacement, and Freeze Protocol

**Status:** Frozen
**Execution stage:** Stage 5, after training and validation data freeze and before any model training

This procedure turns the frozen 60-prompt blueprint into exact test material without letting exact test questions shape the supervised data.

## Entry gates

Authoring cannot begin until:

- the Stage 3 evaluation protocol is independently reviewed and frozen;
- worked examples and prompt-development inputs remain frozen;
- the synthetic Stage 3 retrieval-calibration prompts are registered as excluded source material;
- training and validation examples, split membership, metadata, and identities are frozen;
- photography, tabletop games, and pottery/ceramics are confirmed absent as material topics from all prohibited collections;
- no pilot or full fine-tuning has begun; and
- no held-out model output exists.

## Authoring procedure

1. Create a blank 60-row matrix containing only IDs and the frozen quotas.
2. Randomise matrix-slot authoring order with seed `20260715` and store the complete append-only attempt ledger. Each entry records a global authoring index, within-slot attempt index, slot ID, candidate ID, final status, previous-entry digest, and its own digest. "Earlier candidate" always means a lower stored authoring index, never a lower numeric prompt ID.
3. Draft one candidate at a time to its assigned family, slice, input form, complexity, constraint, robustness role, and withheld-domain fields.
4. Record topic, user goal, requested task/artefact, scenario summary, and important constraints before collision review.
5. Confirm the task is English, single-turn, low-stakes, stable, concise, answerable without tools, and scorable under the frozen rubric.
6. Run exact identity, lexical, semantic, metadata, withheld-domain, and internal-held-out checks.
7. Complete primary and required second reviews under the unseen protocol.
8. Accept the candidate or record a predeclared rejection and author a replacement for the same matrix slot.

Metadata describes the prompt rather than anticipated model behaviour. Input form follows communicative function; composed complexity requires an observable source; ordinary constraint-bearing prompts must be composed and name their constraint. Every family has all three robustness prompts marked composed plus exactly one non-robust composed prompt. The non-robust composed prompt and exactly one robustness prompt per family carry ordinary content constraints. Robustness prompts contain a legitimate underlying task. Cross-domain prompts contain exactly one of the three withheld domains, with every intent-family/domain pair represented once.

## Allowed replacement reasons

A drafted candidate may be replaced only for:

- `scope_or_answerability`;
- `quota_or_metadata`;
- `exact_collision`;
- `semantic_scenario_collision`;
- `withheld_domain_violation`;
- `internal_heldout_collision`; or
- `ambiguous_or_unscorable`.

The replacement log retains candidate ID, complete candidate text and metadata, text identities, matrix slot, reason, rationale, source and retrieved-reference identities, retrieval-report digest, at least two review IDs, replacement status/link, author/reviewer identities, and timestamp. Rejected candidates become a frozen searched source collection rather than disappearing. The freeze bundle binds the ledger entry count and final chain digest and includes a named independent reviewer's explicit complete-history attestation. A candidate is never rejected because a system answered it poorly; no responses exist at this stage.

This is an auditable local control, not a cryptographic proof that an author never drafted an unrecorded prompt. The digest chain prevents silent renumbering after an entry is retained; the separate reviewer attestation makes the completeness claim explicit and attributable. The project must describe that trust boundary honestly.

Every lifecycle timestamp is explicit UTC (`Z`) and may equal another event captured at the same clock resolution. Prohibited source collections freeze and receive their withheld-domain attestations before authoring begins; candidate ledger entries are nondecreasing; reviews follow their candidate and any cited prior review; replacements follow their cited decisions; the complete-ledger attestation follows the last entry; semantic verification follows all source, authoring, attestation, review, and replacement evidence; and the bundle freezes last. Future-dated or reversed histories are invalid.

Frozen supervised data are not modified to rescue a candidate. If a withheld domain appears materially in the frozen training or validation set despite the Stage 4 check, the held-out cross-domain candidate is rejected and the protocol breach is escalated; the domain cannot silently be redefined.

## Reviewer separation

Where practical, the prompt author does not make the final contamination decision. Primary retrieval review may be performed by a blinded model agent; all broad-selection rejections, contamination reject/uncertain decisions, and the seeded six-slot accepted audit receive the separate review defined in the unseen protocol. Reviewer type is recorded honestly. An adversarial reviewer checks the complete set for artificial wording, ambiguous tasks, quota gaming, repeated answer strategies, and scoring feasibility without model outputs.

## Freeze gate

The exact set freezes only when:

- exactly 60 schema-valid metadata records exist with IDs `heldout-v1-001` through `heldout-v1-060`;
- every global, family/slice, family/robustness-role, and family/withheld-domain quota passes;
- all ten constraint-bearing records are composed, carry non-empty constraints, and are two per family;
- all 15 robustness records are composed, with exactly one additional non-robust composed record per family;
- standard/non-constraint records do not carry hidden constraint metadata;
- every exact and semantic review is resolved;
- cross-domain absence has been rechecked against the frozen source collections;
- calibration and protocol verifiers pass;
- replacement, review, collision, and adversarial-review records are complete; and
- prompts and metadata receive a canonical file digest.

The executable Stage 5 validator receives the complete canonical records for worked examples, prompt development, evaluation calibration, training, validation, accepted candidates, and rejected candidates. It recomputes every source identity, candidate/reference text hash, exact match, lexical rank/score, metadata rank/score, and eligible inventory. The canonical semantic generator computes MiniLM scores, ranks, and token diagnostics from those same records; the aggregate validator independently repeats that computation and requires exact equality. The closed `stage5-semantic-review-v1` artifact binds every candidate/source result to the protocol, source identities, generator implementation, and authoring ledger. The bundle hashes that artifact.

The complete-set semantic artifact also contains an independent attestation for every final candidate covering scope, recorded complexity, clear underlying task, answerability, naturalness, scorability, and complete-text review. Every field must pass. Exact normalized matches force rejection and the configured second review. The six audits attach to the final accepted candidate in each preassigned matrix slot. Every replacement is non-self, stays in the same slot, points to that slot's final candidate, cites only reviews of the rejected candidate, and binds the decisive source/reference evidence. The prompt file is not used for development or opened during training configuration. Any later change creates a new version and repeats all checks.

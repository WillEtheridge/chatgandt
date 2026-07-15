# Dataset Contract Adversarial Review

- **Date:** 2026-07-15
- **Reviewer:** Fresh Codex subagent context
- **Scope:** Dataset identity, lifecycle, provenance, rendering, coverage, and split isolation
- **Rounds:** One review and one repair pass
- **Final status:** Material findings resolved in the specification

## Stopping rule

The review considered only findings capable of corrupting training targets, admitting contradictory records, losing material provenance, invalidating coverage or scenario-isolated split claims, or producing non-reproducible rendering. Later authoring quality, semantic audit, tokenizer-aware training, evaluation, and malicious-maintainer hardening were out of scope.

## Findings and resolutions

| Severity | Finding | Resolution |
| --- | --- | --- |
| Blocker | Workflow events hashed the complete record, so later split and pilot assignment changed the digest after terminal acceptance with no valid lifecycle transition | Workflow events now bind a `content_sha256` that excludes only allocation fields; complete allocated records remain bound by freeze identities and the dataset manifest |
| Material | Freeze permitted unresolved candidates alongside 200 accepted examples | Freeze now requires exactly one terminal acceptance or rejection for every candidate and zero unresolved candidates |
| Material | The Qwen prohibition covered initial drafting but not model revision or review | The prohibited-model gate now applies to every frontier-model workflow event |
| Material | A record-only renderer could not know whether a candidate was accepted | The exact target serializer is explicitly pure; public message rendering now requires and validates the record's workflow chain and terminal acceptance |
| Material | Prompt normalization and derived-export ordering were unspecified | Normalization reuses the frozen Stage 3 algorithm; train, validation, and pilot projections are sorted by ascending example ID |
| Material | Mandatory exact split counts contradicted the adopted rule that scenario isolation takes precedence | Exact allocation remains the default; any non-exact allocation requires a bound, recomputed, project-author-approved split-deviation record and cannot waive other gates |

## Proportionality decision

All findings changed the executable meaning of the contract and were repaired. No second adversarial round is warranted: the repaired specification has no known unresolved issue at the agreed materiality threshold. Implementation and tests must now demonstrate the contract rather than extending its assurance boundary.

## Implementation-time compatibility finding

The first implementation attempt placed the new focused suite at `tests/test_dataset.py`, as originally specified. Stage 3 verification intentionally binds the digest of every file matching `tests/test_*.py`; adding a new test therefore made three frozen-evidence checks fail even though the Stage 3 implementation and evidence had not changed.

The contract suite was moved to `contract_tests/test_dataset.py` and given an explicit discovery command. The historical `tests` suite remains byte-identical and continues to use its frozen command. Mutating or recapturing Stage 3 evidence merely to admit later tests would weaken the meaning of that freeze. This compatibility correction changes no dataset rule and does not warrant another adversarial specification round.

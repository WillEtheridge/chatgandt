# ChatG&T Codex agents

These project-scoped agents support bounded Stage 4 dataset production:

- `dataset_author`: creates one initial batch snapshot from a frozen matrix;
- `dataset_reviewer`: performs one independent qualitative review in read-only mode;
- `dataset_reviser`: applies one consolidated, approved repair list; and
- `dataset_auditor`: runs specified mechanical and corpus-level checks in read-only mode.

The root agent remains responsible for batch planning, reviewer independence,
workflow integrity, research-design changes, and deciding whether Stage 4 is
ready to close. Passing reviews are terminalised by deterministic validator
code rather than a human or model acceptance judgment.

## Production loop

1. Root freezes one batch matrix and gives the author exact files and validation commands.
2. Author drafts once and returns a validated snapshot.
3. A fresh reviewer performs one review pass without editing.
4. Root adjudicates findings and freezes one consolidated repair list.
5. Reviser applies that list once.
6. A fresh reviewer performs one terminal review.
7. The deterministic terminalizer records acceptance after every unresolved candidate has an independent pass.
8. Auditor checks achieved coverage and corpus risks before the next matrix is opened.

## Stopping rules

- No agent may spawn another agent; project nesting remains one level deep.
- No batch receives more than one coordinated qualitative repair pass.
- A terminal pass is not reopened for optional polish.
- A persistent failed slot is replaced by a new scenario instead of repeatedly rewritten.
- Rubric, quota, schema, split, or research-design changes are recorded explicitly and never smuggled into candidate edits.
- Agents never commit or push; the root reviews the combined working tree first.
- Exact held-out prompts, model training, and Stage 5 evaluation remain outside this workflow.

Custom-agent configuration is loaded when a new Codex session starts in this
trusted repository.

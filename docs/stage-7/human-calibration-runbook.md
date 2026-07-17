# Stage 7 Project-Author Calibration Runbook

This is the only required human handoff in Stage 7. It measures agreement with the already-sealed primary LLM judgments; it does not replace them, tune the model, or change any response.

The frozen selector achieved 18 qualitative responses rather than the nominal 24 because System A had no schema-valid response and the no-cross-system-fill rule preserves the resulting six-packet shortfall. All 15 planned pairwise comparisons are present, for 33 blind decisions total.

## Collect decisions

From the repository root, run:

```bash
uv run --frozen python scripts/stage7_human_calibration.py collect \
  --packets experiments/evaluations/heldout-evaluation-v1-20260717-run01/derived/human-calibration-packets.jsonl \
  --output experiments/evaluations/heldout-evaluation-v1-20260717-run01/judging/human-calibration-raw.jsonl
```

For a qualitative response, enter one 1–3 score for each frozen dimension. For a pair, enter `a`, `b`, or `tie`. You may add an optional short note. The packet does not reveal either system identity.

The command appends and flushes each answer immediately. If interrupted, run the same command again; it resumes after the completed packet IDs and never rewrites them.

## Handoff

When the command reports `Complete: 33/33`, tell Codex that the calibration is complete. Codex will seal the judgments, validate exact deterministic coverage, calculate human–LLM exact agreement, binary acceptability agreement, weighted Cohen's kappa, and pairwise choice agreement, then finish the Stage 7 report.

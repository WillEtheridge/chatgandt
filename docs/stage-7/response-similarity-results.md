# Stage 7 Response-Similarity Results

**Run:** `heldout-evaluation-v1-20260717-run01`

**Protocol result:** Pass — 240 responses, 5,468 required retrieval-union reviews

## Method

Every held-out response was compared with all frozen worked-example and training responses and with the other 59 outputs from the same system. The canonical response view included every schema field and measurement for valid outputs, or the complete normalised raw output when invalid. Exact matches, lexical top-five neighbours, and pinned MiniLM semantic top-five neighbours formed the review union.

The controller hid system identity, source-collection identity, and exposure status from the reviewer. Complete text pairs were judged in bounded ephemeral Codex contexts using `gpt-5.6-terra` at low reasoning effort. The original two-response batches were reduced after an oversized envelope omitted required keys; incomplete envelopes produced no retained decision. The final reliable boundary used at most five references per context. Across 325 successful contexts, all 5,468 required keys received exactly one retained decision and the canonical aggregate validator recomputed every hash, rank, score, diagnostic, exposure mapping, and coverage requirement.

## Results

There were no exact canonical response matches. Review produced 5,458 `no_concern` decisions and 10 `review_flag` decisions across seven responses.

| System | Exposed-source flags | Within-system flags | Diagnostic-not-exposed flags |
| --- | ---: | ---: | ---: |
| A | 0 | 5 | 0 |
| B | 1 | 1 | 0 |
| C | 2 | 0 | 0 |
| D | 1 | 0 | 0 |

The worked-example flag for B prompt 035 is strong: four method steps and most ingredient concepts reproduce the “Familiar Face” example almost verbatim. D prompt 035 repeats the same distinctive name-repetition and contextual-recall sequence more partially. C prompt 048 shares a map-centred Mara story structure with training example 126, while C prompt 050 closely parallels the old-room-to-new-room notice in training example 069. These are review flags, not binary proof of memorisation.

A's five within-system flags concern generic long-form self-improvement lists, especially response 031. B had one shorter within-system ingredient-and-method template recurrence. No exact generic collapse occurred.

## Interpretation

The audit distinguishes treatment exposure from generic resemblance. B and D were directly exposed to worked examples at inference; C and D were exposed to training examples through the adapter. A's within-system repetition cannot be attributed to project data and illustrates generic base-model template collapse. Conversely, the B prompt-035 case demonstrates that a strong prompt can secure behavioural compliance by copying a demonstration too literally.

The audit covers only known project examples. It cannot inspect Qwen's pretraining corpus and makes no claim that an output is novel relative to unknown external data.

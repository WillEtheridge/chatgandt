# Dataset v1 Production Batch 03 Plan

- **Stage:** 4, Step 8
- **Status:** Closed; 20 independently reviewed candidates terminally accepted
- **Batch:** `dataset-v1-batch-03`
- **Planned candidates:** 20 (`dataset-v1-031`–`dataset-v1-050`)
- **Prior accepted corpus:** 30 examples, six per intent family
- **Matrix:** [`production-matrix.json`](../data/dataset-v1/authoring/batch-03/production-matrix.json)
- **Authoring standard:** `chatgnt-dataset-authoring-v1.3`

## Coverage shape

Batch 03 contains four slots per family: three target-use and one robustness slot. Each family adds one question, two direct requests, and one statement or fragment; two standard and two composed examples; and two compatible-constraint examples. The robustness roles deliberately add roles underrepresented in the first 30 accepted examples.

The scenarios prioritise task subtypes and topics that are absent or sparse within their family. The batch does not reproduce the complete final ratio in isolation; it makes measured progress toward the frozen per-family targets while retaining room for later correction.

## Boundaries

- The matrix freezes scenario identity and metadata before exact drafting.
- Exact user prompts must include all supplied material required by the response.
- Photography, tabletop games, and pottery or ceramics remain excluded.
- No exact held-out prompt, Qwen output, split assignment, or model-performance signal may be used.
- One fresh author drafts the batch; a separate fresh reviewer judges it once.
- At most one consolidated repair pass and one terminal review are allowed.
- Passing candidates are terminalised by `chatgnt-dataset-terminalizer-v1`; no human acceptance is required.

## Production evidence

The first whole-batch author exceeded its bounded reporting window and was stopped. The unchanged frozen matrix was then divided into two non-overlapping ten-slot authoring assignments. Each half produced canonical candidates and draft events, passed authoring validation independently, and was mechanically assembled before combined validation.

The independent review passed 19 candidates and requested one local factual correction for `dataset-v1-049`: the delivered water-cycle summary incorrectly made condensation cool vapour rather than making cooling the condition that causes condensation. One bounded revision corrected only that sentence while preserving the single-sentence constraint and all four named stages. A fresh terminal reviewer passed the repaired snapshot.

The deterministic terminalizer then accepted all 20 candidates and an immediate idempotence run proposed zero additions.

Final evidence:

- matrix SHA-256: `b065395ecfb4a4dc100cb14b72b54be401624f95a1bfee29f38cf88e13a5be9f`;
- candidate SHA-256: `9c7ba19dc0b63cfc2ab1ba74bf77a636b43002dea71d098231f75b9955838697`;
- workflow-event SHA-256: `6243aae8e811bb9769e3d0402a7a7013b59d5bdafa7684d7adb454d92de20b65`;
- lifecycle: 20 accepted, 0 rejected, 0 unresolved;
- coverage: four candidates per family, 15 target-use, five robustness, 10 standard, 10 composed, and 10 constraint-bearing;
- review: 19 initial passes, one bounded revision, one terminal pass;
- terminal acceptance events: `dataset-event-v1-0239` through `dataset-event-v1-0258`;
- authoring validator: pass with no warnings; and
- terminalizer dry run, write, and idempotence run: pass.

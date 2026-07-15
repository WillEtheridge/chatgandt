# Unseen and Contamination Protocol

**Protocol:** `chatgnt-evaluation-v1`
**Status:** Frozen
**Applies to:** worked examples, prompt-development prompts, training data, validation data, and the future held-out set

This protocol defines the project-specific meaning of "unseen." It cannot establish that a prompt or topic was absent from Qwen's unknown pretraining corpus. It establishes that the exact held-out task was not used to build, tune, select, or revise ChatG&T within this project.

## Operational boundary

A held-out candidate is not sufficiently unseen when it is:

1. an exact match after the frozen normalization procedure;
2. a close paraphrase of an existing project prompt;
3. a superficially changed version of the same scenario; or
4. a task whose substantive answer could be reused after changing only names, objects, or minor details.

Shared domain or task form is allowed when the user goal and required substantive content are genuinely different. Similarity created by the experiment itself is ignored: every response uses the same JSON contract and cocktail behaviour, and repeated explanation, transformation, creative, or robustness task forms are intentional.

For a candidate and a retrieved reference, the semantic reviewer answers independently:

1. Do they have substantially the same user goal?
2. Do they contain substantially the same situation, concept, supplied source, or requested artefact?
3. Could the substantive answer be reused with only surface changes?

Three `yes` answers mean `reject`. Any `no` means `allow`. A question that cannot be answered confidently produces `uncertain`, not a forced decision.

## Collections checked

Every held-out candidate is checked against:

- all five-shot worked-example inputs;
- all spent prompt-development inputs;
- all Stage 3 similarity-calibration inputs, which are synthetic tooling cases rather than reusable project examples;
- every frozen training input;
- every frozen validation input; and
- all earlier accepted held-out candidates; and
- all rejected held-out candidates, so a collision cannot simply be proposed again.

The stored seeded authoring schedule is the sole definition of "earlier". The validator derives accepted/rejected eligibility from that schedule and its final-candidate flag, then compares it with the complete canonical source records. Caller-supplied counts, hashes, ranks, and source identities are insufficient evidence.

The three cross-domain topics—photography, tabletop games, and pottery/ceramics—must additionally be absent as material subject matter from worked examples, prompt development, training, and validation. The 15 cross-domain slots form a complete three-domain by five-intent-family matrix. General words such as "game," "clay," or "camera-ready" do not by themselves establish topic presence; the recorded metadata and substantive scenario determine it.

Each source/domain absence check is a human attestation, not a digital signature. Its digest is deterministically recomputed over the bound source identity and content digest, domain, decision, reviewer identity, attestation statement, and notes. Changing any of those fields invalidates the record. This makes the claim attributable and tamper-evident inside the repository while retaining the ordinary local trust boundary of a portfolio project.

## Frozen normalization and exact identity

The original UTF-8 prompt receives an SHA-256 digest. A second digest is computed after:

1. Unicode NFC normalization;
2. CRLF and CR line endings converted to LF;
3. Unicode-aware case folding;
4. all whitespace runs collapsed to one ASCII space; and
5. outer whitespace removed.

Punctuation is preserved because quotes, code, paths, and supplied text can be meaningful. Matching normalized digests are automatic rejection candidates. A second reviewer still verifies the source identity and retained record; exact matching does not bypass the audit trail.

## Candidate retrieval, not automatic classification

Every candidate receives neighbours from three independent signals, calculated separately inside each frozen source collection so a large source cannot crowd out a small one:

- **Lexical:** top five per source by `rapidfuzz.fuzz.token_ratio` after frozen normalization, or all eligible records when fewer than five exist.
- **Semantic:** top five per source by cosine similarity from the pinned MiniLM implementation, or all eligible records when fewer than five exist.
- **Metadata:** up to five records per source sharing the most fields among topic, user goal, requested task or artefact, scenario summary, and important constraints.

Duplicate neighbours are merged and every contributing signal is retained. There is no similarity threshold for automatic approval or rejection. RapidFuzz reorders and compares tokens, so it is useful for surface edits but cannot decide whether two scenarios require the same answer. MiniLM can retrieve paraphrases but also makes false-positive thematic matches and false-negative fine distinctions. Automation only gives the reviewer a short, reproducible list.

### Pinned semantic implementation

- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`
- Runtime: the project's pinned `transformers` and `torch` packages
- Tokenization: padding and truncation enabled with `max_length=256`
- Pooling: multiply the final hidden state by the expanded attention mask, sum across tokens, divide by the mask count clamped to `1e-9`
- Vector normalization: L2
- Similarity: cosine
- Output dimensions: 384

The implementation deliberately follows the model card's Transformers example rather than introducing the `sentence-transformers` package. The 256 limit is **wordpieces, not words or characters**. Content beyond the first 256 wordpieces does not influence the embedding. Stage 5 must record each prompt's pre-truncation wordpiece count and a `semantic_input_truncated` flag. Any truncated candidate or reference receives manual supplied-content review in addition to the retrieved neighbours. This matters especially for transformation and serialization prompts containing quoted text or code.

The calibration set includes short obvious, paraphrased, disguised, acceptable-same-domain, creative, transformation, and robustness cases. It must also include a supplied-text case longer than 256 wordpieces and verify the truncation diagnostic. The production gate is recall@5 of 12/12 for both lexical and semantic retrieval. Retrieval recall on this synthetic calibration is a tooling diagnostic, not evidence that the semantic rule is accurate in production.

The Stage 5 aggregate validator recomputes exact, lexical, metadata, and MiniLM evidence. The executable semantic generator and validator share the same pinned model-loading, batching, pooling, normalization, token-diagnostic, cosine-ranking, and tie-order implementation. The closed artifact binds the complete candidate/source matrix, exact model revision, source digests, authoring schedule, generator implementation, and captured result. Stored ranks and scores are evidence to verify, not caller assertions to trust.

## Review and replacement

- Every `reject` and `uncertain` decision receives a second review.
- Every rejection during broad selection or answerability review also receives a second review; early rejection cannot bypass the audit trail.
- A deterministic 10% sample of accepted matrix slots receives a second review: the six lowest SHA-256 ranks of `contamination-audit-v1|20260715|preassigned_matrix_prompt_id`. Selection uses the preassigned `heldout-v1-NNN` slot, so rejecting and replacing a candidate cannot change whether that slot is audited.
- The second reviewer sees the candidate, reference, and frozen rule, but not the first decision or rationale.
- Agreement finalises the result.
- Disagreement is adjudicated with both original rationales retained.
- Unresolved uncertainty is handled conservatively: reject and replace the held-out candidate.

Two model-agent reviews are labelled as such and are not described as independent human experts. Prompt evidence is retained in closed `prompt-overlap-review-v1` records. Response-similarity evidence uses a separate schema because its questions and claims differ.

The training and validation data are already frozen at that point. A collision therefore replaces the held-out candidate; supervised data are not rewritten around a known exam question. Rejections use only the predeclared reasons in the authoring protocol.

## Calibration gate

Before held-out authoring begins:

1. the calibration JSONL must satisfy its record contract;
2. every deliberately paired lexical and semantic match must appear within its respective top-five list, with recall reported separately rather than required to be perfect;
3. exact identity and metadata retrieval tests must pass;
4. the over-256-wordpiece case must report truncation; and
5. a reviewer must confirm that the frozen three-question decisions match the calibration labels.

A failed retrieval diagnostic prompts investigation of the retriever or calibration corpus. It does not permit changing the semantic collision rule after seeing held-out outputs.

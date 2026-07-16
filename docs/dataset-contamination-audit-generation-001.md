# Dataset Contamination Audit Generation 001

- **Date:** 2026-07-16
- **Generation:** `generation-001`
- **Status:** Machine evidence valid; review deliberately not started because the frozen workload is disproportionate
- **Original path:** `data/dataset-v1/audit/v1/generation-001/` (generated payload removed after the hashes and counts below were retained)

The atomic production build and read-only generation verifier passed. The generation reports zero automatic failures, but its immutable flag set contains 41,957 owner pairs from 158,587 retrieval triggers:

- 122,400 lexical triggers;
- 35,200 semantic triggers;
- 986 metadata triggers; and
- one withheld-lexicon trigger.

The flag-set SHA-256 is `f21b7fde8a809363932593cda1f964e1abc686a699a4b5e9594b01d71574d7a9`. The generation-manifest SHA-256 reported by the verifier is `828f5cfaa1ce80c3c0995762a0cce6557405fd59f7fc7a8998516d8ce32c4f87`.

## Why review stopped

The frozen specification applied the Stage 3 top-five retrieval rule separately to every eligible view and source collection. At 200 supervised records, many response components, and numerous development-output collections, that produced thousands of low-information nearest-neighbour pairs. Ingredient names alone contributed 38,655 triggers; method steps contributed 28,402.

Writing 41,957 supposedly independent human-readable dispositions would reward rubber-stamping and obscure the small number of genuinely informative record-level comparisons. No dispositions or attestations were created, and no finalization was attempted.

## Resolution

The project deliberately abandoned this generated workload rather than manufacture 41,957 low-value dispositions. The 149 MB payload was untracked, was not a dataset source, and was removed after this report retained its result, counts, and content identities. The specification, adversarial review, implementation review, and this failure report remain as process evidence.

D-059 replaces the design with one bounded record-level audit. This is an explicit post-generation protocol change, not a claim that generation 001 passed.

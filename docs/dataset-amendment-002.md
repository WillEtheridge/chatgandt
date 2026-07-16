# Dataset Amendment 002

- **Date:** 2026-07-16
- **Active dataset identity:** `chatgnt-dataset-v1.2`
- **Manifest:** `data/dataset-v1/amendments/amendment-002/manifest.json`
- **Status:** Applied, audited, and frozen

## Why it was needed

The first split attempt reached the frozen-dataset validator and stopped because ingredient counts seven and eight were absent. The original dataset had contained both, but amendment 001 had unknowingly superseded the only examples carrying them. This was a real contract failure, not a reason to rerun the allocator or weaken the rule.

Amendment 002 preserves the scenarios, prompts, metadata, methods, and substantive answers of `dataset-v1-201` and `dataset-v1-202` while replacing them with separately accepted `dataset-v1-208` and `dataset-v1-209`. Their ingredient lists contain seven and eight coherent measures respectively.

The v1.1 view remains reproducible. The amendment manifest binds that active view's identities, both new files, and the two supersession mappings. The ordinary authoring validator passes both replacement histories, and the active v1.2 view contains exactly 200 accepted examples.

## Verification

The unchanged bounded contamination audit passed v1.2. The frozen-dataset validator then passed the first deterministic split with no exception or deviation.

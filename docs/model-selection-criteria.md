# Model-Selection Criteria

This record defines how ChatG&T candidate models will be screened and compared before individual models are researched. Defining the criteria first reduces the risk of changing the requirements to favour an attractive candidate.

## Selection method

Candidate models are assessed in two stages:

1. **Eligibility gates:** a candidate that fails a hard requirement is excluded from the main shortlist.
2. **Comparative preferences:** eligible candidates are compared using evidence relevant to this experiment.

The preferences will not initially be collapsed into an arbitrary weighted score. Material trade-offs will remain visible in the comparison.

## Eligibility gates

### Model type and size

- The model must be open-weight and instruction-tuned.
- The normal search range is approximately **1–3 billion parameters**.
- A model outside that range requires a compelling practical advantage and must still satisfy the compute and deployment constraints.

### Licence and redistribution

The model terms must clearly permit:

- downloading and local inference;
- fine-tuning;
- distribution of the resulting LoRA adapter;
- public interactive deployment; and
- commercial use.

Research-only, non-commercial, unclear, or deployment-incompatible terms are disqualifying. Required attribution, notices, inherited adapter conditions, and separate acceptable-use terms must be recorded.

### Baseline capability

The model must provide a meaningful prompt-engineering baseline. Under a competent structured-output prompt, it must demonstrate:

- useful and coherent answers to varied short prompts;
- reasonable multi-part instruction following;
- the ability to produce raw JSON without application-level repair; and
- at least some adherence to an exact schema.

Perfect ChatG&T behaviour is not required before fine-tuning. Candidate checks are for experimental suitability, not an unrecorded search for the model that already performs ChatG&T best.

### LoRA and ecosystem compatibility

The model must support a reproducible workflow using standard causal-language-model tooling in Hugging Face Transformers and PEFT, including:

- adding LoRA adapters to suitable modules;
- mixed-precision training on rented NVIDIA hardware;
- saving and reloading the adapter separately from the base weights; and
- running inference with the trained adapter.

The project may use ordinary LoRA or QLoRA depending on measured memory requirements. Substantial model-specific training engineering is outside the intended scope.

### Context capacity

- The model must support at least **8,192 tokens** of context.
- The final five-shot instructions, schema, examples, representative user prompt, generated response allowance, and a documented safety margin must all fit without truncation.
- The actual token budget must later be calculated with the selected model's tokenizer.

### Lifecycle feasibility

The model must:

- fit the audited local environment for development and CPU correctness checks;
- have a LoRA training path within the **$20 one-off compute budget**; and
- have at least one credible public-serving path within the **$10 monthly hosting budget**.

Free CPU deployment is a hypothesis to measure, not a guaranteed requirement. A shared-GPU or scale-to-zero fallback is acceptable within budget.

## Comparative preferences

Eligible models will be compared on:

- general instruction-following quality at their size;
- raw JSON and schema-following reliability under prompting;
- concise generation without repetition or trailing prose;
- clarity and permissiveness of the licence;
- quality of the official model card and chat-template documentation;
- use of `safetensors` and no dependency on custom remote code;
- maturity of Transformers, PEFT, quantisation, and serving support;
- measured local and hosted memory use;
- measured time to first token and generation latency;
- availability of practical CPU quantisation or export paths;
- adapter size and simplicity of adapter loading or merging; and
- reproducibility through stable identifiers and pinnable revisions.

## Feasibility-check boundary

Shortlisted models will later be checked using a small disposable diagnostic set that is separate from:

- the five-shot prompt-development set;
- training and validation data; and
- the frozen held-out evaluation set.

These checks may test general usefulness, raw JSON generation, basic schema adherence, repetition, loading, memory use, and latency. They must not be presented as final ChatG&T results.


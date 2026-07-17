# Stage 7 Judge Calibration Assessment

- **Calibration evidence:** `reviews/stage7-judge-calibration-20260717.json`
- **Judge identity:** `openai-codex-cli-gpt-5.6-terra`
- **Exposed model ID:** `gpt-5.6-terra`
- **Fresh contexts:** 6/6
- **Status:** Complete before held-out generation; proceed with disclosed limitations

## Result

The judge matched two of six complete calibration anchors exactly. Across the four qualitative packets, seven of 12 individual 1–3 scores matched exactly and ten of 12 matched at the frozen acceptable-versus-fail boundary. One of two pairwise choices matched exactly.

The disagreements were not hidden or used to rewrite the anchors:

- the behaviour-pressure response was scored `2/2/2` rather than `3/2/3`, retaining a joint pass but showing a conservative strength threshold;
- the compatible-constraint response received an underlying-answer failure because the judge interpreted shadowing and self-talk as speaking practice rather than genuinely conversational activities;
- the dimension-boundary response received metaphor `2` rather than `1`, while its underlying-answer failure and recipe score matched; and
- the intended pairwise tie was awarded narrowly to Response B because the judge found a slight practical advantage.

The format-pressure case and clear pairwise-preference case matched exactly.

## Decision

Proceed without altering the frozen rubric, anchors, system treatments, or judging instruction. The protocol deliberately sets no arbitrary agreement threshold that retrospectively validates or invalidates the experiment. Trying alternative judge configurations until one reproduced every anchor would introduce evaluator-selection bias.

The calibration shows two limitations that the final report must keep visible: the primary judge may score strong responses conservatively, and it may turn a small perceived advantage into a winner rather than a tie. Headline conclusions must therefore retain structural results separately, show the later project-author calibration agreement, report ties explicitly, and avoid presenting judge-derived differences as objective ground truth.

## Operational note

An initial pre-evidence invocation named an unsupported GPT-5 Codex model and was rejected by the service before any decision or file was produced. The successful calibration bound the exact available `gpt-5.6-terra` identity. Each packet ran in a distinct ephemeral, read-only, no-project context; the controller added only an output-envelope instruction and retained the frozen substantive instruction and packet bytes.

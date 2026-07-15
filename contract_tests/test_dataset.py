from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
from io import StringIO
import tempfile
import unittest
from unittest.mock import patch

from chatgnt.dataset import (
    content_sha256,
    load_canonical_jsonl,
    load_dataset_contract,
    render_assistant_target,
    render_training_messages,
    validate_authoring_dataset,
    validate_example,
    validate_frozen_dataset,
    validate_workflow_event,
    verify_dataset_contract,
)
from chatgnt.records import ContractError, canonical_line
from scripts.verify_dataset_contract import main as contract_cli


CONTRACT = load_dataset_contract()
FAMILIES = CONTRACT["registries"]["intent_families"]
TOPICS = CONTRACT["registries"]["topics"]
VALIDATION_INDEXES = {0, 10, 24, 32, 34, 36, 38, 39}


def example(number: int = 1, *, family: str = FAMILIES[0], index: int = 0, split: str | None = None, pilot: bool = False) -> dict:
    if index < 28:
        coverage = "target_use"
    elif index < 34:
        coverage = "breadth"
    else:
        coverage = "robustness"
    input_form = "question" if index < 10 else "direct_request_or_command" if index < 30 else "statement_or_fragment"
    composed = index >= 24
    constrained = 24 <= index <= 35
    sources = []
    if constrained:
        sources.append("ordinary_content_constraint")
    if coverage == "robustness":
        sources.append("robustness_pressure")
    role = None
    if coverage == "robustness":
        role = CONTRACT["registries"]["robustness_roles"][(index - 34) // 2]
    ingredient_count = 3 + index % 6
    return {
        "record_schema_version": 1,
        "example_id": f"dataset-v1-{number:03d}",
        "scenario_id": f"scenario-synthetic-{number:03d}",
        "user_prompt": f"Synthetic prompt {number}?",
        "assistant_response": {
            "title": f"Synthetic Recipe {number}",
            "ingredients": [{"amount": value + 1, "unit": "ml", "name": f"ingredient {value + 1}"} for value in range(ingredient_count)],
            "method": ["Combine the useful details carefully.", "Serve the result in a clear form."],
            "garnish": "A small practical flourish.",
        },
        "metadata": {
            "intent_family": family,
            "coverage_slice": coverage,
            "input_form": input_form,
            "complexity": "composed" if composed else "standard",
            "complexity_sources": sources,
            "constraint_bearing": constrained,
            "robustness_role": role,
            "topic": TOPICS[index % len(TOPICS)],
            "task_subtype": CONTRACT["registries"]["task_subtypes_by_family"][family][index % 8],
            "user_goal": "obtain a synthetic but useful answer",
            "requested_task_or_artefact": "a synthetic response",
            "scenario_summary": f"Synthetic scenario {number} for contract testing.",
            "important_constraints": ["Retain the synthetic constraint."] if constrained else [],
        },
        "provenance": {
            "authoring_batch_id": "dataset-v1-batch-01",
            "initial_draft_source": "human",
            "initial_draft_model_id": None,
            "model_revision_used": False,
            "material_human_edit": False,
        },
        "split": split,
        "pilot_member": pilot,
    }


def chain(item: dict, start: int = 1, *, accepted: bool = True) -> list[dict]:
    digest = content_sha256(item)
    common = {"record_schema_version": 1, "example_id": item["example_id"], "content_sha256": digest, "actor_type": "human", "actor_identity": "test-author", "model_id": None, "reason_codes": []}
    draft = common | {"event_id": f"dataset-event-v1-{start:04d}", "prior_event_id": None, "event_type": "draft_created", "recorded_at_utc": "2026-07-15T10:00:00Z", "outcome": "created", "notes": "Created."}
    review = common | {"event_id": f"dataset-event-v1-{start + 1:04d}", "prior_event_id": draft["event_id"], "event_type": "quality_review", "recorded_at_utc": "2026-07-15T10:01:00Z", "outcome": "pass", "notes": "Passed."}
    if accepted:
        terminal = common | {"event_id": f"dataset-event-v1-{start + 2:04d}", "prior_event_id": review["event_id"], "event_type": "accepted", "recorded_at_utc": "2026-07-15T10:02:00Z", "outcome": "accepted", "notes": "Accepted."}
    else:
        terminal = common | {"event_id": f"dataset-event-v1-{start + 2:04d}", "prior_event_id": review["event_id"], "event_type": "rejected", "recorded_at_utc": "2026-07-15T10:02:00Z", "outcome": "rejected", "reason_codes": ["coverage_mismatch"], "notes": "Rejected for coverage."}
    return [draft, review, terminal]


def frozen_fixture() -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict]]:
    candidates = []
    events = []
    number = 1
    event_number = 1
    for family in FAMILIES:
        pilot_indexes = [value for value in range(40) if value not in VALIDATION_INDEXES][:8]
        for index in range(40):
            item = example(number, family=family, index=index, split="validation" if index in VALIDATION_INDEXES else "train", pilot=index in pilot_indexes)
            candidates.append(item)
            events.extend(chain(item, event_number))
            number += 1
            event_number += 3
    train = sorted((item for item in candidates if item["split"] == "train"), key=lambda item: item["example_id"])
    validation = sorted((item for item in candidates if item["split"] == "validation"), key=lambda item: item["example_id"])
    pilot = sorted((item for item in candidates if item["pilot_member"]), key=lambda item: item["example_id"])
    return candidates, events, train, validation, pilot


class DatasetContractTests(unittest.TestCase):
    def test_contract_mode_and_schema_parity(self):
        report = verify_dataset_contract()
        self.assertEqual(report["result"], "pass")
        self.assertEqual(report["targets"], {"accepted": 200, "train": 160, "validation": 40, "pilot": 40})

    def test_cli_canonical_success_and_contract_failure(self):
        stdout = StringIO()
        with patch("sys.stdout", stdout):
            self.assertEqual(contract_cli(["--mode", "contract"]), 0)
        self.assertTrue(stdout.getvalue().startswith('{"built_in_lifecycle":"pass"'))
        self.assertTrue(stdout.getvalue().endswith("\n"))
        stderr = StringIO()
        with patch("sys.stderr", stderr):
            self.assertEqual(contract_cli(["--mode", "authoring"]), 2)
        self.assertTrue(stderr.getvalue().startswith('{"error":'))
        self.assertIn('"result":"fail"', stderr.getvalue())

    def test_strict_canonical_jsonl_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.jsonl"
            value = {"a": 1}
            path.write_bytes(canonical_line(value))
            self.assertEqual(load_canonical_jsonl(path), [value])
            bad_values = [b'{"a":1,"a":2}\n', b"\n", b"\xef\xbb\xbf{}\n", b"{}\r\n", b'{"a": 1}\n', b"NaN\n", b"{}"]
            for raw in bad_values:
                with self.subTest(raw=raw):
                    path.write_bytes(raw)
                    with self.assertRaises(ContractError):
                        load_canonical_jsonl(path)

    def test_example_cross_fields_trimming_and_target_model_gate(self):
        item = example()
        validate_example(item, CONTRACT, mode="authoring")
        changes = [
            ("robustness", lambda value: value["metadata"].update(coverage_slice="robustness")),
            ("standard sources", lambda value: value["metadata"]["complexity_sources"].append("connected_steps")),
            ("constraint", lambda value: value["metadata"].update(constraint_bearing=True)),
            ("pilot", lambda value: value.update(pilot_member=True)),
            ("trim", lambda value: value["assistant_response"].update(title=" bad")),
            ("subtype", lambda value: value["metadata"].update(task_subtype="concept_explanation")),
        ]
        for name, mutate in changes:
            broken = deepcopy(item)
            mutate(broken)
            with self.subTest(name=name), self.assertRaises(ContractError):
                validate_example(broken, CONTRACT, mode="authoring")
        model = deepcopy(item)
        model["provenance"].update(initial_draft_source="frontier_model", initial_draft_model_id="qwen2.5-1.5b-instruct")
        with self.assertRaisesRegex(ContractError, "prohibited"):
            validate_example(model, CONTRACT, mode="authoring")

    def test_event_invariants_and_target_model_gate(self):
        item = example(split="train")
        events = chain(item)
        for event in events:
            validate_workflow_event(event, CONTRACT)
        broken = deepcopy(events[1])
        broken.update(actor_type="frontier_model", model_id="Qwen/Qwen2.5-1.5B-Instruct")
        with self.assertRaisesRegex(ContractError, "prohibited"):
            validate_workflow_event(broken, CONTRACT)
        broken = deepcopy(events[1])
        broken.update(outcome="revision_requested", reason_codes=[], notes="")
        with self.assertRaises(ContractError):
            validate_workflow_event(broken, CONTRACT)

    def test_authoring_lifecycle_and_rendering(self):
        item = example(split="train")
        events = chain(item)
        report = validate_authoring_dataset([item], events, CONTRACT)
        self.assertEqual(report["lifecycle"]["accepted"], 1)
        messages = render_training_messages(item, events, CONTRACT)
        self.assertEqual(messages[0], {"role": "system", "content": ""})
        self.assertEqual(messages[1]["content"], item["user_prompt"])
        self.assertEqual(messages[2]["content"], render_assistant_target(item))
        self.assertTrue(messages[2]["content"].startswith('{"title":'))
        self.assertIn('"ingredients":[{"amount":1,"unit":"ml","name":"ingredient 1"}', messages[2]["content"])
        broken_events = deepcopy(events)
        broken_events[-1]["prior_event_id"] = broken_events[0]["event_id"]
        with self.assertRaises(ContractError):
            validate_authoring_dataset([item], broken_events, CONTRACT)
        unresolved = events[:-1]
        item["split"] = None
        with self.assertRaises(ContractError):
            render_training_messages(item, unresolved, CONTRACT)

        accepted_unassigned = example(2)
        unassigned_events = chain(accepted_unassigned, 4)
        report = validate_authoring_dataset([accepted_unassigned], unassigned_events, CONTRACT)
        self.assertEqual(report["lifecycle"]["accepted"], 1)
        with self.assertRaisesRegex(ContractError, "assigned train or validation split"):
            render_training_messages(accepted_unassigned, unassigned_events, CONTRACT)

    def test_freeze_exact_projection_and_hard_targets(self):
        values = frozen_fixture()
        report = validate_frozen_dataset(*values, CONTRACT)
        self.assertTrue(report["allocation_exact"])
        self.assertEqual(report["allocation"]["train"], 160)
        drifted = list(values[2])
        drifted.reverse()
        with self.assertRaisesRegex(ContractError, "ordered"):
            validate_frozen_dataset(values[0], values[1], drifted, values[3], values[4], CONTRACT)

    def test_nonexact_split_requires_bound_approved_deviation(self):
        candidates, events, train, validation, pilot = frozen_fixture()
        moved = next(item for item in candidates if item["metadata"]["intent_family"] == FAMILIES[0] and item["split"] == "train" and not item["pilot_member"])
        moved["split"] = "validation"
        train = sorted((item for item in candidates if item["split"] == "train"), key=lambda item: item["example_id"])
        validation = sorted((item for item in candidates if item["split"] == "validation"), key=lambda item: item["example_id"])
        with self.assertRaisesRegex(ContractError, "split-deviation"):
            validate_frozen_dataset(candidates, events, train, validation, pilot, CONTRACT)
        expected = {
            "train": 160, "validation": 40, "pilot": 40,
            "per_intent_family": {family: {"train": 32, "validation": 8, "pilot": 8} for family in FAMILIES},
        }
        achieved = deepcopy(expected)
        achieved.update(train=159, validation=41)
        achieved["per_intent_family"][FAMILIES[0]].update(train=31, validation=9)
        digest = lambda records: hashlib.sha256(b"".join(canonical_line(item) for item in records)).hexdigest()
        deviation = {
            "record_schema_version": 1, "deviation_id": "dataset-split-deviation-v1", "dataset_contract_id": "chatgnt-dataset-v1",
            "candidates_sha256": digest(candidates), "train_sha256": digest(train), "validation_sha256": digest(validation), "pilot_sha256": digest(pilot),
            "expected_counts": expected, "achieved_counts": achieved, "reason": "scenario_group_indivisibility",
            "affected_scenario_ids": [moved["scenario_id"]], "rationale": "The indivisible scenario group prevents the exact family allocation.",
            "approved_by": "project-author", "approved_at_utc": "2026-07-15T20:00:00Z",
        }
        report = validate_frozen_dataset(candidates, events, train, validation, pilot, CONTRACT, split_deviation=deviation)
        self.assertFalse(report["allocation_exact"])
        deviation["train_sha256"] = "0" * 64
        with self.assertRaisesRegex(ContractError, "train_sha256"):
            validate_frozen_dataset(candidates, events, train, validation, pilot, CONTRACT, split_deviation=deviation)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from copy import deepcopy
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from chatgnt.dataset import content_sha256
from chatgnt.dataset_split import assign_dataset_splits, load_split_config, verify_split_config, write_allocation
from chatgnt.records import ContractError, canonical_line
from scripts.assign_dataset_splits import main as split_cli
from test_dataset import CONTRACT, FAMILIES, chain, frozen_fixture


SPLIT_CONFIG = load_split_config()


def allocation_fixture() -> tuple[list[dict], list[dict]]:
    candidates, events, _, _, _ = frozen_fixture()
    for item in candidates:
        item["split"] = None
        item["pilot_member"] = False
    return candidates, events


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_bytes(b"".join(canonical_line(item) for item in records))


def refresh_event_digests(candidates: list[dict], events: list[dict]) -> None:
    digest_by_id = {item["example_id"]: content_sha256(item) for item in candidates}
    for event in events:
        event["content_sha256"] = digest_by_id[event["example_id"]]


class DatasetSplitTests(unittest.TestCase):
    def test_configuration_and_exact_reproducible_allocation(self):
        self.assertEqual(verify_split_config()["result"], "pass")
        candidates, events = allocation_fixture()
        original = deepcopy(candidates)
        first = assign_dataset_splits(candidates, events, CONTRACT, SPLIT_CONFIG)
        second = assign_dataset_splits(candidates, events, CONTRACT, SPLIT_CONFIG)
        self.assertEqual(candidates, original)
        self.assertEqual(first, second)
        self.assertTrue(first["report"]["allocation_exact"])
        self.assertFalse(first["report"]["split_deviation_required"])
        self.assertEqual(len(first["train"]), 160)
        self.assertEqual(len(first["validation"]), 40)
        self.assertEqual(len(first["pilot"]), 40)
        self.assertEqual({value["pilot"] for value in first["report"]["per_intent_family"].values()}, {8})

    def test_scenarios_never_cross_splits(self):
        candidates, events = allocation_fixture()
        candidates[1]["scenario_id"] = candidates[0]["scenario_id"]
        refresh_event_digests(candidates, events)
        result = assign_dataset_splits(candidates, events, CONTRACT, SPLIT_CONFIG)
        split_by_scenario: dict[str, set[str]] = {}
        for item in result["candidates"]:
            if item["split"] is not None:
                split_by_scenario.setdefault(item["scenario_id"], set()).add(item["split"])
        self.assertTrue(all(len(values) == 1 for values in split_by_scenario.values()))

    def test_cross_family_scenario_and_preallocation_are_rejected(self):
        candidates, events = allocation_fixture()
        candidates[40]["scenario_id"] = candidates[0]["scenario_id"]
        refresh_event_digests(candidates, events)
        with self.assertRaisesRegex(ContractError, "spans intent families"):
            assign_dataset_splits(candidates, events, CONTRACT, SPLIT_CONFIG)
        candidates, events = allocation_fixture()
        candidates[0]["split"] = "train"
        with self.assertRaisesRegex(ContractError, "unallocated"):
            assign_dataset_splits(candidates, events, CONTRACT, SPLIT_CONFIG)

    def test_indivisible_groups_produce_visible_nonexact_allocation(self):
        candidates, events = allocation_fixture()
        family_records = [item for item in candidates if item["metadata"]["intent_family"] == FAMILIES[0]]
        for index, item in enumerate(family_records):
            group = index // 3
            item["scenario_id"] = f"scenario-indivisible-{group:02d}"
        refresh_event_digests(candidates, events)
        result = assign_dataset_splits(candidates, events, CONTRACT, SPLIT_CONFIG)
        self.assertFalse(result["report"]["allocation_exact"])
        self.assertTrue(result["report"]["split_deviation_required"])
        self.assertNotEqual(result["report"]["per_intent_family"][FAMILIES[0]]["validation"], 8)
        self.assertTrue(result["report"]["deviation_scenario_ids"])

    def test_unresolved_candidate_is_rejected(self):
        candidates, events = allocation_fixture()
        events = [item for item in events if not (item["example_id"] == candidates[0]["example_id"] and item["event_type"] == "accepted")]
        with self.assertRaisesRegex(ContractError, "unresolved"):
            assign_dataset_splits(candidates, events, CONTRACT, SPLIT_CONFIG)

    def test_cli_dry_run_and_atomic_write(self):
        candidates, events = allocation_fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_path = root / "candidates.jsonl"
            event_path = root / "events.jsonl"
            output = root / "allocated"
            write_jsonl(candidate_path, candidates)
            write_jsonl(event_path, events)
            stdout = StringIO()
            with patch("sys.stdout", stdout):
                code = split_cli(["--candidates", str(candidate_path), "--events", str(event_path)])
            self.assertEqual(code, 0)
            self.assertFalse(output.exists())
            with patch("sys.stdout", StringIO()):
                code = split_cli(["--candidates", str(candidate_path), "--events", str(event_path), "--output-dir", str(output)])
            self.assertEqual(code, 0)
            self.assertEqual(
                {item.name for item in output.iterdir()},
                {"candidates.jsonl", "workflow-events.jsonl", "train.jsonl", "validation.jsonl", "pilot.jsonl", "allocation-report.json"},
            )
            with self.assertRaisesRegex(ContractError, "already exists"):
                write_allocation(assign_dataset_splits(candidates, events, CONTRACT, SPLIT_CONFIG), output)


if __name__ == "__main__":
    unittest.main()

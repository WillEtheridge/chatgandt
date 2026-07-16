from __future__ import annotations

from copy import deepcopy
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from chatgnt.dataset import content_sha256, load_canonical_jsonl, load_dataset_contract, validate_authoring_dataset, validate_workflow_event
from chatgnt.dataset_terminalization import terminalize_passing_reviews, write_events_atomically
from chatgnt.records import ContractError, canonical_line
from scripts.finalize_dataset_batch import main as terminalize_cli

from contract_tests.test_dataset import chain, example


CONTRACT = load_dataset_contract()
STAMP = "2026-07-16T12:00:00Z"


class DatasetTerminalizationTests(unittest.TestCase):
    def test_automated_acceptance_is_valid_but_frontier_acceptance_is_not(self):
        item = example()
        events = chain(item)[:2]
        events[1].update(actor_type="frontier_model", actor_identity="independent-reviewer", model_id="gpt-5.6-terra")
        result = terminalize_passing_reviews([item], events, CONTRACT, recorded_at_utc=STAMP)
        terminal = result["added_events"][0]
        self.assertEqual(terminal["actor_type"], "automated_validator")
        self.assertIsNone(terminal["model_id"])
        validate_workflow_event(terminal, CONTRACT)
        broken = deepcopy(terminal)
        broken.update(actor_type="frontier_model", model_id="gpt-5.6-sol")
        with self.assertRaises(ContractError):
            validate_workflow_event(broken, CONTRACT)
        broken = deepcopy(terminal)
        broken["model_id"] = "gpt-5.6-sol"
        with self.assertRaises(ContractError):
            validate_workflow_event(broken, CONTRACT)

    def test_automated_acceptance_requires_independent_reviewer(self):
        item = example()
        events = chain(item)[:2]
        with self.assertRaisesRegex(ContractError, "independent"):
            terminalize_passing_reviews([item], events, CONTRACT, recorded_at_utc=STAMP)

    def test_every_unresolved_candidate_must_have_a_final_pass(self):
        first, second = example(1), example(2)
        events = chain(first)[:2] + chain(second, 3)[:2]
        for event in events:
            if event["event_type"] == "quality_review":
                event.update(actor_identity="independent-reviewer")
        events[-1].update(outcome="revision_requested", reason_codes=["recipe_execution_weak"], notes="Needs revision.")
        with self.assertRaisesRegex(ContractError, "dataset-v1-002"):
            terminalize_passing_reviews([first, second], events, CONTRACT, recorded_at_utc=STAMP)

    def test_cli_is_dry_run_by_default_and_writes_atomically(self):
        item = example()
        events = chain(item)[:2]
        events[1].update(actor_identity="independent-reviewer")
        with tempfile.TemporaryDirectory() as directory:
            candidates_path = Path(directory) / "candidates.jsonl"
            events_path = Path(directory) / "events.jsonl"
            candidates_path.write_bytes(canonical_line(item))
            events_path.write_bytes(b"".join(canonical_line(event) for event in events))
            candidate_bytes = candidates_path.read_bytes()
            original = events_path.read_bytes()
            with patch("sys.stdout", StringIO()):
                self.assertEqual(terminalize_cli(["--candidates", str(candidates_path), "--events", str(events_path), "--recorded-at-utc", STAMP]), 0)
            self.assertEqual(events_path.read_bytes(), original)
            with patch("sys.stdout", StringIO()):
                self.assertEqual(terminalize_cli(["--candidates", str(candidates_path), "--events", str(events_path), "--recorded-at-utc", STAMP, "--write"]), 0)
            written = load_canonical_jsonl(events_path)
            self.assertEqual(len(written), 3)
            self.assertEqual(validate_authoring_dataset([item], written, CONTRACT)["lifecycle"]["accepted"], 1)
            accepted_bytes = events_path.read_bytes()
            with patch("sys.stdout", StringIO()):
                self.assertEqual(terminalize_cli(["--candidates", str(candidates_path), "--events", str(events_path), "--recorded-at-utc", STAMP, "--write"]), 0)
            self.assertEqual(events_path.read_bytes(), accepted_bytes)
            self.assertEqual(candidates_path.read_bytes(), candidate_bytes)

    def test_atomic_write_refuses_concurrent_event_drift(self):
        item = example()
        events = chain(item)[:2]
        events[1].update(actor_identity="independent-reviewer")
        result = terminalize_passing_reviews([item], events, CONTRACT, recorded_at_utc=STAMP)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            original = b"".join(canonical_line(event) for event in events)
            path.write_bytes(original + b"\n")
            with self.assertRaisesRegex(ContractError, "changed after validation"):
                write_events_atomically(path, result["events"], expected_existing_bytes=original)


if __name__ == "__main__":
    unittest.main()

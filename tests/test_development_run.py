import json
from pathlib import Path
import tempfile
import unittest

from chatgnt.development_run import (
    DEVELOPMENT_AB_SCHEDULE_V1,
    DEVELOPMENT_AB_SCHEDULE_V1_SHA256,
    DEVELOPMENT_AB_RUN_PLAN_V1_SHA256,
    DEVELOPMENT_RUN_SEED,
    validate_development_schedule,
    validate_development_run_plan,
)
from chatgnt.records import ContractError


class DevelopmentRunPlanTests(unittest.TestCase):
    def test_committed_plan_freezes_seed_and_input_identities(self):
        result = validate_development_run_plan()
        self.assertEqual(result["result"], "pass")
        self.assertEqual(result["sha256"], DEVELOPMENT_AB_RUN_PLAN_V1_SHA256)
        self.assertEqual(result["run_seed"], DEVELOPMENT_RUN_SEED)
        self.assertEqual(result["derived_execution_order_seed"], 17625029341685692511)
        self.assertEqual(result["schedule_attempt_count_when_built"], 40)

    def test_changed_seed_and_unknown_fields_are_rejected_before_path_resolution(self):
        source = {
            "schema_version": 1,
            "run_plan_id": "development-ab-v1",
            "prompt_set_path": "unused",
            "system_set_path": "unused",
            "run_seed": DEVELOPMENT_RUN_SEED,
            "primary_samples_per_system_prompt": 1,
        }
        changed_seed = dict(source, run_seed=7)
        unknown_field = dict(source, note="extra")
        mutations = [
            (changed_seed, "run_seed must equal frozen value"),
            (unknown_field, "key mismatch"),
        ]

        for index, (value, expected_error) in enumerate(mutations):
            with self.subTest(mutation=index):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "run-plan.json"
                    path.write_text(json.dumps(value) + "\n")
                    with self.assertRaisesRegex(ContractError, expected_error):
                        validate_development_run_plan(path)


class DevelopmentScheduleTests(unittest.TestCase):
    def test_committed_schedule_has_complete_paired_coverage(self):
        result = validate_development_schedule()
        self.assertEqual(result["result"], "pass")
        self.assertEqual(result["sha256"], DEVELOPMENT_AB_SCHEDULE_V1_SHA256)
        self.assertEqual(result["attempt_count"], 40)
        self.assertEqual(result["system_attempt_counts"], {"A": 20, "B": 20})
        self.assertEqual(result["complete_ab_pair_count"], 20)
        self.assertEqual(result["paired_generation_seed_count"], 20)
        self.assertTrue(result["attempt_indices_contiguous"])
        self.assertTrue(result["production_scheduler_exact_match"])

    def test_changed_attempt_order_is_rejected(self):
        source = json.loads(DEVELOPMENT_AB_SCHEDULE_V1.read_text())
        source["schedule"]["attempts"][0], source["schedule"]["attempts"][1] = (
            source["schedule"]["attempts"][1],
            source["schedule"]["attempts"][0],
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "schedule.json"
            path.write_text(json.dumps(source) + "\n")
            with self.assertRaisesRegex(ContractError, "differs from the production-derived"):
                validate_development_schedule(path)


if __name__ == "__main__":
    unittest.main()

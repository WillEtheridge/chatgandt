import json
from pathlib import Path
import tempfile
import unittest

from chatgnt.prompting import (
    DEVELOPMENT_AB_SYSTEM_SET_V1,
    DEVELOPMENT_AB_SYSTEM_SET_V1_SHA256,
    DEVELOPMENT_B_SYSTEM_SET_V3,
    DEVELOPMENT_B_SYSTEM_SET_V3_SHA256,
    FINAL_CHECK_V2,
    FINAL_CHECK_V3,
    FINAL_REMINDER,
    FIVE_SHOT_PROMPT_V1,
    FIVE_SHOT_PROMPT_V1_SHA256,
    FIVE_SHOT_PROMPT_V2,
    FIVE_SHOT_PROMPT_V2_SHA256,
    FIVE_SHOT_PROMPT_V3,
    FIVE_SHOT_PROMPT_V3_SHA256,
    FIVE_SHOT_PROMPT_V4,
    FIVE_SHOT_PROMPT_V4_SHA256,
    MINIMAL_PROMPT_V1,
    MINIMAL_PROMPT_V1_SHA256,
    load_instruction_text,
    render_five_shot_content,
    render_five_shot_content_v2,
    render_five_shot_content_v3,
    render_five_shot_content_v4,
    validate_five_shot_prompt,
    validate_five_shot_prompt_v2,
    validate_five_shot_prompt_v3,
    validate_five_shot_prompt_v4,
    validate_development_ab_system_set,
    validate_development_b_v3_system_set,
    validate_minimal_prompt,
)
from chatgnt.records import ContractError


class FiveShotPromptTests(unittest.TestCase):
    def test_committed_prompt_is_exact_deterministic_assembly(self):
        result = validate_five_shot_prompt()
        self.assertEqual(result["result"], "pass")
        self.assertEqual(result["sha256"], FIVE_SHOT_PROMPT_V1_SHA256)
        self.assertEqual(result["worked_example_count"], 5)
        self.assertTrue(result["deterministic_assembly"])

    def test_render_has_five_labelled_examples_and_final_reminder(self):
        content = render_five_shot_content()
        self.assertEqual(content.count("\nUser input:\n"), 5)
        self.assertEqual(content.count("\nAssistant output:\n"), 5)
        self.assertTrue(content.endswith(FINAL_REMINDER))
        asset = json.loads(FIVE_SHOT_PROMPT_V1.read_text())
        self.assertEqual(asset["content"], content)

    def test_changed_asset_and_noncanonical_instruction_source_are_rejected(self):
        source = json.loads(FIVE_SHOT_PROMPT_V1.read_text())
        source["content"] += " changed"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset_path = root / "prompt.json"
            asset_path.write_text(json.dumps(source, ensure_ascii=False) + "\n")
            with self.assertRaisesRegex(ContractError, "differs from deterministic"):
                validate_five_shot_prompt(asset_path)

            instruction_path = root / "instructions.txt"
            instruction_path.write_bytes(b"instruction\n\n")
            with self.assertRaisesRegex(ContractError, "exactly one terminal newline"):
                load_instruction_text(instruction_path)

    def test_v2_is_deterministic_and_changes_only_the_closing_control(self):
        result = validate_five_shot_prompt_v2()
        v1 = render_five_shot_content()
        v2 = render_five_shot_content_v2()
        self.assertEqual(result["sha256"], FIVE_SHOT_PROMPT_V2_SHA256)
        self.assertEqual(json.loads(FIVE_SHOT_PROMPT_V2.read_text())["content"], v2)
        self.assertTrue(v1.endswith(FINAL_REMINDER))
        self.assertEqual(v2, v1[: -len(FINAL_REMINDER)] + FINAL_CHECK_V2)

    def test_v3_is_deterministic_and_changes_only_the_closing_control(self):
        result = validate_five_shot_prompt_v3()
        v1 = render_five_shot_content()
        v3 = render_five_shot_content_v3()
        self.assertEqual(result["sha256"], FIVE_SHOT_PROMPT_V3_SHA256)
        self.assertEqual(json.loads(FIVE_SHOT_PROMPT_V3.read_text())["content"], v3)
        self.assertEqual(v3, v1[: -len(FINAL_REMINDER)] + FINAL_CHECK_V3)

    def test_v4_keeps_worked_examples_and_v3_shape_cue(self):
        result = validate_five_shot_prompt_v4()
        v3 = render_five_shot_content_v3()
        v4 = render_five_shot_content_v4()
        self.assertEqual(result["sha256"], FIVE_SHOT_PROMPT_V4_SHA256)
        self.assertEqual(json.loads(FIVE_SHOT_PROMPT_V4.read_text())["content"], v4)
        self.assertEqual(
            v3.split("BEGIN WORKED EXAMPLES", 1)[1],
            v4.split("BEGIN WORKED EXAMPLES", 1)[1],
        )


class MinimalPromptTests(unittest.TestCase):
    def test_committed_asset_is_the_frozen_empty_system_condition(self):
        result = validate_minimal_prompt()
        self.assertEqual(result["result"], "pass")
        self.assertEqual(result["sha256"], MINIMAL_PROMPT_V1_SHA256)
        self.assertEqual(result["content_character_count"], 0)
        self.assertEqual(result["worked_example_count"], 0)
        self.assertTrue(result["explicit_empty_system_message"])

    def test_nonempty_content_is_rejected(self):
        source = json.loads(MINIMAL_PROMPT_V1.read_text())
        source["content"] = "You are helpful."
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "minimal.json"
            path.write_text(json.dumps(source) + "\n")
            with self.assertRaisesRegex(ContractError, "differs from the explicit empty-system contract"):
                validate_minimal_prompt(path)


class DevelopmentSystemSetTests(unittest.TestCase):
    def test_committed_set_maps_base_only_systems_to_frozen_prompts(self):
        result = validate_development_ab_system_set()
        self.assertEqual(result["result"], "pass")
        self.assertEqual(result["sha256"], DEVELOPMENT_AB_SYSTEM_SET_V1_SHA256)
        self.assertEqual(result["system_ids"], ["A", "B"])
        self.assertEqual(result["adapter_enabled"], {"A": False, "B": False})
        self.assertTrue(result["untouched_base_runtime_only"])

    def test_changed_or_incorrect_mapping_is_rejected(self):
        source = json.loads(DEVELOPMENT_AB_SYSTEM_SET_V1.read_text())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prompts = root / "prompts"
            prompts.symlink_to(MINIMAL_PROMPT_V1.parent, target_is_directory=True)

            wrong_mapping = json.loads(json.dumps(source))
            wrong_mapping["systems"][1]["prompt_asset_path"] = "../prompts/minimal-v1.json"
            path = root / "systems" / "systems.json"
            path.parent.mkdir()
            path.write_text(json.dumps(wrong_mapping) + "\n")
            with self.assertRaisesRegex(ContractError, "five-shot asset invariant"):
                validate_development_ab_system_set(path)

            path.write_text(json.dumps(source, separators=(",", ":")) + "\n")
            with self.assertRaisesRegex(ContractError, "differs from frozen development A/B system-set digest"):
                validate_development_ab_system_set(path)

    def test_selected_v3_set_contains_only_untuned_system_b(self):
        result = validate_development_b_v3_system_set()
        self.assertEqual(result["sha256"], DEVELOPMENT_B_SYSTEM_SET_V3_SHA256)
        self.assertEqual(result["system_ids"], ["B"])
        self.assertEqual(result["prompt_assets"]["B"]["prompt_asset_id"], "five-shot-v3")
        self.assertTrue(result["formal_confirmation_candidate"])

    def test_changed_selected_v3_mapping_is_rejected(self):
        source = json.loads(DEVELOPMENT_B_SYSTEM_SET_V3.read_text())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prompts = root / "prompts"
            prompts.symlink_to(FIVE_SHOT_PROMPT_V3.parent, target_is_directory=True)
            path = root / "systems" / "systems.json"
            path.parent.mkdir()
            path.write_text(json.dumps(source, separators=(",", ":")) + "\n")
            with self.assertRaisesRegex(ContractError, "differs from frozen development B/v3 system-set digest"):
                validate_development_b_v3_system_set(path)


if __name__ == "__main__":
    unittest.main()

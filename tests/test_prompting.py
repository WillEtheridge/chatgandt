import json
from pathlib import Path
import tempfile
import unittest

from chatgnt.prompting import (
    DEVELOPMENT_AB_SYSTEM_SET_V1,
    DEVELOPMENT_AB_SYSTEM_SET_V1_SHA256,
    FINAL_REMINDER,
    FIVE_SHOT_PROMPT_V1,
    FIVE_SHOT_PROMPT_V1_SHA256,
    MINIMAL_PROMPT_V1,
    MINIMAL_PROMPT_V1_SHA256,
    load_instruction_text,
    render_five_shot_content,
    validate_five_shot_prompt,
    validate_development_ab_system_set,
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


if __name__ == "__main__":
    unittest.main()

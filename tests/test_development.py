import json
from pathlib import Path
import tempfile
import unittest

from chatgnt.development import (
    DEVELOPMENT_PROMPTS_V1,
    DEVELOPMENT_PROMPTS_V1_SHA256,
    WORKED_EXAMPLES_V1,
    WORKED_EXAMPLES_V1_SHA256,
    validate_development_prompts,
    validate_worked_examples,
)
from chatgnt.records import ContractError


class DevelopmentPromptTests(unittest.TestCase):
    def test_committed_v1_set_passes_closed_contract(self):
        result = validate_development_prompts()
        self.assertEqual(result["result"], "pass")
        self.assertEqual(result["prompt_count"], 20)
        self.assertEqual(result["sha256"], DEVELOPMENT_PROMPTS_V1_SHA256)
        self.assertTrue(result["family_role_pairs_complete"])
        self.assertTrue(result["canonical_jsonl"])

    def test_metadata_and_identifier_contracts_are_closed(self):
        records = [json.loads(line) for line in DEVELOPMENT_PROMPTS_V1.read_text().splitlines()]
        mutations = []

        unexpected_key = json.loads(json.dumps(records))
        unexpected_key[0]["metadata"]["topic"] = "career"
        mutations.append(unexpected_key)

        unknown_tag = json.loads(json.dumps(records))
        unknown_tag[0]["metadata"]["challenge_tags"] = ["unknown"]
        mutations.append(unknown_tag)

        wrong_id = json.loads(json.dumps(records))
        wrong_id[0]["prompt_id"] = "dev-v1-wrong-clean"
        mutations.append(wrong_id)

        for records_with_error in mutations:
            with self.subTest(mutation=mutations.index(records_with_error)):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "prompts.jsonl"
                    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for record in records_with_error))
                    with self.assertRaises(ContractError):
                        validate_development_prompts(path)

    def test_noncanonical_serialization_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prompts.jsonl"
            path.write_text(DEVELOPMENT_PROMPTS_V1.read_text() + "\n")
            with self.assertRaisesRegex(ContractError, "not canonically serialized"):
                validate_development_prompts(path)


class WorkedExampleTests(unittest.TestCase):
    def test_committed_examples_pass_closed_contract(self):
        result = validate_worked_examples()
        self.assertEqual(result["result"], "pass")
        self.assertEqual(result["worked_example_count"], 5)
        self.assertEqual(result["sha256"], WORKED_EXAMPLES_V1_SHA256)
        self.assertTrue(result["intent_families_complete"])
        self.assertTrue(result["all_responses_schema_valid"])

    def test_example_record_and_response_contracts_are_closed(self):
        source = json.loads(WORKED_EXAMPLES_V1.read_text())
        mutations = []

        unexpected_key = json.loads(json.dumps(source))
        unexpected_key["worked_examples"][0]["topic"] = "memory"
        mutations.append((unexpected_key, "key mismatch"))

        wrong_role = json.loads(json.dumps(source))
        wrong_role["worked_examples"][0]["development_role"] = "robustness"
        mutations.append((wrong_role, "expected 'clean'"))

        invalid_response = json.loads(json.dumps(source))
        invalid_response["worked_examples"][0]["assistant_response"]["ingredients"][0]["amount"] = 0
        mutations.append((invalid_response, "non_positive_amount"))

        for index, (value, expected_error) in enumerate(mutations):
            with self.subTest(mutation=index):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "examples.json"
                    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
                    with self.assertRaisesRegex(ContractError, expected_error):
                        validate_worked_examples(path)

    def test_semantically_valid_content_change_requires_a_new_version(self):
        source = json.loads(WORKED_EXAMPLES_V1.read_text())
        source["worked_examples"][0]["assistant_response"]["title"] = "A Different Title"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "examples.json"
            path.write_text(json.dumps(source, ensure_ascii=False, indent=2) + "\n")
            with self.assertRaisesRegex(ContractError, "differs from frozen worked-examples v1 digest"):
                validate_worked_examples(path)


if __name__ == "__main__":
    unittest.main()

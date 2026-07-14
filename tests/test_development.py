import json
from pathlib import Path
import tempfile
import unittest

from chatgnt.development import (
    DEVELOPMENT_PROMPTS_V1,
    DEVELOPMENT_PROMPTS_V1_SHA256,
    validate_development_prompts,
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


if __name__ == "__main__":
    unittest.main()

import json
from pathlib import Path
import tempfile
import unittest

from chatgnt.records import canonical_line
from chatgnt.structural_evaluation import evaluate_structure


VALID = {
    "title": "The Test",
    "ingredients": [
        {"amount": 50, "unit": "ml", "name": "clarity"},
        {"amount": 25, "unit": "ml", "name": "care"},
        {"amount": 1, "unit": "dash", "name": "wit"},
    ],
    "method": ["Combine the useful parts.", "Serve the answer clearly."],
    "garnish": "One practical next step.",
}


class StructuralEvaluationTests(unittest.TestCase):
    def test_writes_derived_results_without_mutating_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = root / "run"
            run.mkdir()
            prompts = canonical_line({"prompt_id": "p1", "prompt": "Help.", "metadata": {}})
            (run / "prompts.jsonl").write_bytes(prompts)
            raw = json.dumps(VALID, ensure_ascii=False)
            response = {
                "run_id": "run-1",
                "attempt_index": 0,
                "prompt_id": "p1",
                "system_id": "B",
                "attempt_status": "success",
                "raw_output": raw,
                "raw_output_sha256": __import__("hashlib").sha256(raw.encode()).hexdigest(),
            }
            source = canonical_line(response)
            (run / "responses.jsonl").write_bytes(source)
            output = root / "evaluation"

            summary = evaluate_structure(run, output)

            self.assertEqual((run / "responses.jsonl").read_bytes(), source)
            self.assertEqual(summary["systems"]["B"]["schema_valid"], 1)
            self.assertEqual(len((output / "validations.jsonl").read_text().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()

import json
from pathlib import Path
import tempfile
import unittest

from chatgnt.blind_scoring import prepare_blind_packets, reveal_and_summarize_scores
from chatgnt.records import canonical_line


class BlindScoringTests(unittest.TestCase):
    def test_packets_hide_source_identity_and_mapping_retains_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = root / "run"
            evaluation = root / "evaluation"
            run.mkdir()
            evaluation.mkdir()
            (run / "prompts.jsonl").write_bytes(
                canonical_line({"prompt_id": "p1", "prompt": "Help me.", "metadata": {}})
            )
            (run / "responses.jsonl").write_bytes(
                canonical_line(
                    {
                        "run_id": "source-run",
                        "attempt_index": 0,
                        "prompt_id": "p1",
                        "system_id": "B",
                        "raw_output": "candidate",
                    }
                )
            )
            (evaluation / "validations.jsonl").write_bytes(
                canonical_line(
                    {
                        "source_run_id": "source-run",
                        "attempt_index": 0,
                        "prompt_id": "p1",
                        "system_id": "B",
                        "source_raw_output_sha256": "0" * 64,
                        "validation": {"schema_valid": True},
                    }
                )
            )
            output = root / "blind"
            result = prepare_blind_packets([("secret-source", run, evaluation)], output)
            packet = json.loads((output / "packets.jsonl").read_text())
            mapping = json.loads((output / "identity-mapping.jsonl").read_text())

            self.assertEqual(result["packet_count"], 1)
            self.assertNotIn("secret-source", json.dumps(packet))
            self.assertNotIn("source-run", json.dumps(packet))
            self.assertEqual(mapping["source_label"], "secret-source")
            self.assertEqual(mapping["blind_id"], packet["blind_id"])

            (output / "scores.jsonl").write_bytes(
                canonical_line(
                    {
                        "blind_id": packet["blind_id"],
                        "evaluator": "test judge",
                        "underlying_answer_quality": 2,
                        "metaphorical_coherence": 3,
                        "recipe_style_execution": 2,
                        "full_qualitative_pass": True,
                    }
                )
            )
            summary = reveal_and_summarize_scores(output)
            self.assertEqual(summary["sources"]["secret-source"]["full_qualitative_pass"], 1)


if __name__ == "__main__":
    unittest.main()

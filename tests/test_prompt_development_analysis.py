from pathlib import Path
import tempfile
import unittest

from chatgnt.configuration import PROJECT_ROOT
from chatgnt.prompt_development_analysis import summarize_prompt_versions
from chatgnt.records import read_strict_json


class PromptDevelopmentAnalysisTests(unittest.TestCase):
    def test_committed_summary_reproduces_from_retained_evidence(self):
        development = PROJECT_ROOT / "experiments" / "development" / "local"
        evaluations = PROJECT_ROOT / "experiments" / "evaluations"
        versions = [
            (
                f"v{number}",
                f"local-v{number}",
                development / f"five-shot-v{number}-ollama-q4km-20260715",
                evaluations / f"five-shot-v{number}-ollama-q4km-20260715-structure",
                evaluations / f"five-shot-v{number}-blind-scoring",
            )
            for number in range(1, 5)
        ]
        expected, _ = read_strict_json(
            evaluations / "prompt-development-summary-v1.json"
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "summary.json"
            actual = summarize_prompt_versions(versions, output)
            reloaded, _ = read_strict_json(output)
        self.assertEqual(actual, expected)
        self.assertEqual(reloaded, expected)
        self.assertEqual(actual["selected_version"], "v3")
        self.assertTrue(actual["formal_confirmation_required"])


if __name__ == "__main__":
    unittest.main()

"""Deployment-only tests kept outside the frozen experimental test identity."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from chatgnt.configuration import adapter_identity, load_project_configuration, load_prompt_asset
from chatgnt.live_service import LiveContractError, LiveService
from chatgnt.records import GenerationResult
from chatgnt.validation import load_response_schema
from scripts.package_hf_adapter import DEFAULT_SOURCE, SOURCE_ADAPTER_DIGEST, package as package_adapter
from scripts.package_hf_space import FILES, package as package_space


VALID_RECIPE = json.dumps({
    "title": "The Test Pour",
    "ingredients": [
        {"amount": 50, "unit": "ml", "name": "useful answer"},
        {"amount": 25, "unit": "ml", "name": "clear structure"},
        {"amount": 1, "unit": "dash", "name": "wit"},
    ],
    "method": ["Mix the evidence.", "Serve the conclusion."],
    "garnish": "One concrete next step.",
})


def generation_result(raw_output: str) -> GenerationResult:
    return GenerationResult(
        "success", ({"role": "system", "content": ""}, {"role": "user", "content": "prompt"}),
        "rendered", (1,), 1, (2,), 1, 1, raw_output, "0" * 64, "eos_token", 151645,
        False, 1_000_000, None,
    )


class StubEngine:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = iter(outputs)
        self.requests = []

    def generate(self, request, profile, timing):
        self.requests.append(request)
        return generation_result(next(self.outputs))


class DeploymentTests(unittest.TestCase):
    def service(self, base_outputs: list[str], adapted_outputs: list[str]):
        root = Path(__file__).resolve().parents[2]
        base = StubEngine(base_outputs)
        adapted = StubEngine(adapted_outputs)
        service = LiveService(
            base,
            adapted,
            load_project_configuration(),
            load_prompt_asset(root / "config/prompts/five-shot-v3.json"),
            load_prompt_asset(root / "config/prompts/minimal-v1.json"),
            load_response_schema(),
            adapter_revision="adapter-revision",
            adapter_digest="0" * 64,
        )
        return service, base, adapted

    def test_spirit_guide_uses_only_system_c(self) -> None:
        service, base, adapted = self.service([], [VALID_RECIPE])
        response = service.spirit_guide("A useful prompt", "request-1")
        self.assertEqual(response["outcome"]["status"], "valid")
        self.assertEqual(base.requests, [])
        self.assertEqual(adapted.requests[0].system_id, "C")

    def test_tasting_uses_matched_seeds_and_randomised_mapping(self) -> None:
        service, base, adapted = self.service([VALID_RECIPE], [VALID_RECIPE])
        with patch("chatgnt.live_service.secrets.randbits", return_value=123), patch(
            "chatgnt.live_service.secrets.randbelow", return_value=0
        ):
            response = service.tasting_room("A useful prompt", "request-2")
        self.assertEqual(base.requests[0].system_id, "B")
        self.assertEqual(adapted.requests[0].system_id, "C")
        self.assertEqual(base.requests[0].generation_seed, adapted.requests[0].generation_seed)
        self.assertEqual(response["fineTunedAnswer"], 1)

    def test_model_format_failures_remain_outcomes(self) -> None:
        service, _, _ = self.service([], ["```json\n{}\n```", '{"title":"only"}'])
        self.assertEqual(service.spirit_guide("First", "request-3")["outcome"]["failure"], "invalid-json")
        self.assertEqual(service.spirit_guide("Second", "request-4")["outcome"]["failure"], "invalid-schema")

    def test_rejects_oversized_input_before_generation(self) -> None:
        service, _, adapted = self.service([], [])
        with self.assertRaises(LiveContractError):
            service.spirit_guide("x" * 501, "request-5")
        self.assertEqual(adapted.requests, [])

    def test_adapter_package_preserves_weights_and_rewrites_metadata(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temporary:
            output = Path(temporary) / "adapter"
            result = package_adapter(DEFAULT_SOURCE, output)
            config = json.loads((output / "adapter_config.json").read_text())
            self.assertEqual(config["base_model_name_or_path"], "Qwen/Qwen2.5-1.5B-Instruct")
            self.assertTrue(result["weights_unchanged"])
            self.assertNotEqual(result["publication_adapter_digest"], SOURCE_ADAPTER_DIGEST)
            self.assertEqual(adapter_identity(output)["adapter_digest"], result["publication_adapter_digest"])

    def test_space_package_contains_only_allowlisted_files(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temporary:
            output = Path(temporary) / "space"
            files = package_space(output)
            inference = (output / "chatgnt/inference.py").read_text()
        expected = tuple(sorted((*FILES, "README.md", "app.py", "requirements.txt")))
        self.assertEqual(files, expected)
        self.assertNotIn("experiments", "\n".join(files))
        self.assertIn('low_cpu_mem_usage=False, torch_device="cpu"', inference)
        self.assertIn("parameter.requires_grad_(False)", inference)


if __name__ == "__main__":
    unittest.main()

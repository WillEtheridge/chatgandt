import json
from pathlib import Path
import tempfile
import unittest

from chatgnt.configuration import (
    MODEL_FILE_NAMES, adapter_identity, load_project_configuration, load_prompt_asset,
    load_prompts, load_system_set, verify_model_files,
)
from chatgnt.identity import file_identity, sha256_file, tree_digest
from chatgnt.records import ContractError, canonical_line


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_line(value))


class ProjectConfigurationTests(unittest.TestCase):
    def test_committed_configs_match_frozen_values(self):
        config = load_project_configuration()
        self.assertEqual(config.primary_profile.profile_id, "primary-sampled-v1")
        self.assertEqual(config.primary_profile.max_new_tokens, 512)
        self.assertTrue(config.timing_policy.canonical)

    def test_closed_schema_rejects_unknown_key(self):
        source = Path("config")
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            for name in ("model.toml", "generation.toml", "inference.toml"):
                (target / name).write_bytes((source / name).read_bytes())
            (target / "model.toml").write_text((target / "model.toml").read_text() + "\nextra = true\n")
            with self.assertRaises(ContractError):
                load_project_configuration(target)


class InputTests(unittest.TestCase):
    def test_prompt_preserves_content_and_defaults_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "p.jsonl"
            path.write_bytes(b'{"prompt_id":"p1","prompt":"  caf\xc3\xa9  "}\n\n')
            prompts, _ = load_prompts(path)
            self.assertEqual(prompts[0].prompt, "  café  ")
            self.assertEqual(prompts[0].metadata, {})

    def test_prompt_duplicate_ids_and_bad_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "p.jsonl"
            path.write_text('{"prompt_id":"p","prompt":"x"}\n{"prompt_id":"p","prompt":"y"}\n')
            with self.assertRaises(ContractError): load_prompts(path)
            path.write_text('{"prompt_id":"p","prompt":"x","metadata":[]}\n')
            with self.assertRaises(ContractError): load_prompts(path)

    def test_bom_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "p.jsonl"; path.write_bytes(b"\xef\xbb\xbf{}\n")
            with self.assertRaises(ContractError): load_prompts(path)

    def test_every_system_invariant_and_adapter_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "minimal.json", {"schema_version": 1, "prompt_asset_id": "minimal", "version": "1", "worked_example_count": 0, "content": ""})
            write(root / "five.json", {"schema_version": 1, "prompt_asset_id": "five", "version": "1", "worked_example_count": 5, "content": "five examples"})
            systems = {"schema_version": 1, "systems": [
                {"system_id": "D", "prompt_asset_path": "five.json", "adapter_enabled": True},
                {"system_id": "A", "prompt_asset_path": "minimal.json", "adapter_enabled": False},
                {"system_id": "C", "prompt_asset_path": "minimal.json", "adapter_enabled": True},
                {"system_id": "B", "prompt_asset_path": "five.json", "adapter_enabled": False}]}
            write(root / "systems.json", systems)
            parsed, _ = load_system_set(root / "systems.json", root / "adapter")
            self.assertEqual([x.system_id for x in parsed], list("ABCD"))
            with self.assertRaises(ContractError): load_system_set(root / "systems.json", None)
            systems["systems"][0]["adapter_enabled"] = False; write(root / "systems.json", systems)
            with self.assertRaises(ContractError): load_system_set(root / "systems.json", root / "adapter")

    def test_adapter_forbidden_for_base_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); write(root / "minimal.json", {"schema_version": 1, "prompt_asset_id": "minimal", "version": "1", "worked_example_count": 0, "content": ""})
            write(root / "systems.json", {"schema_version": 1, "systems": [{"system_id": "A", "prompt_asset_path": "minimal.json", "adapter_enabled": False}]})
            with self.assertRaises(ContractError): load_system_set(root / "systems.json", root / "adapter")

    def test_model_file_manifest_verification_and_corruption(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); snapshot = root / "snapshot"; snapshot.mkdir()
            files = []
            for index, name in enumerate(MODEL_FILE_NAMES):
                (snapshot / name).write_bytes(bytes([index]))
                files.append(file_identity(snapshot / name, snapshot))
            manifest = {"schema_version": 1, "model_id": "Qwen/Qwen2.5-1.5B-Instruct", "revision": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306", "files": files}
            write(root / "manifest.json", manifest)
            self.assertEqual(verify_model_files(snapshot, root / "manifest.json"), files)
            (snapshot / "config.json").write_bytes(b"changed")
            with self.assertRaises(ContractError): verify_model_files(snapshot, root / "manifest.json")

    def test_unprovenanced_adapter_requires_explicit_diagnostic_bypass(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); write(root / "adapter_config.json", {"r": 8}); (root / "adapter.safetensors").write_bytes(b"weight")
            with self.assertRaises(ContractError): adapter_identity(root)
            identity = adapter_identity(root, True)
            self.assertEqual(identity["adapter_id"], "lora-lifecycle-diagnostic")


if __name__ == "__main__": unittest.main()

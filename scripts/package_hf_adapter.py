#!/usr/bin/env python3
"""Build the deterministic, publishable ChatG&T adapter bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from chatgnt.configuration import EXPECTED_MODEL, adapter_identity  # noqa: E402
from chatgnt.identity import file_identity, sha256_file, tree_digest  # noqa: E402


DEFAULT_SOURCE = ROOT / "experiments/training/full-training-v1/full-candidate-3-v1-20260717-run01/adapter"
DEFAULT_OUTPUT = ROOT / "artifacts/deployment/hf-model"
CARD_TEMPLATE = ROOT / "deployment/huggingface/model/README.md"
SOURCE_ADAPTER_DIGEST = "0eef1d5da017a18f571a5e37cc152d1351bfbda9f0d343c3f376a1f68a2d4249"


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def write_json(path: Path, value: object) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def package(source: Path, output: Path) -> dict[str, object]:
    source = source.resolve()
    output = output.resolve()
    if source == output or ROOT not in output.parents:
        raise ValueError("output must be a separate directory inside the project")
    source_evidence = adapter_identity(source)
    if source_evidence["adapter_digest"] != SOURCE_ADAPTER_DIGEST:
        raise ValueError("source adapter digest does not match Candidate 3")

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for name in ("adapter_config.json", "adapter_model.safetensors", "adapter-provenance.json"):
        shutil.copy2(source / name, output / name)

    source_config_sha = sha256_file(source / "adapter_config.json")
    config = json.loads((output / "adapter_config.json").read_text(encoding="utf-8"))
    config["base_model_name_or_path"] = EXPECTED_MODEL["base_model"]["id"]
    config["revision"] = EXPECTED_MODEL["base_model"]["revision"]
    write_json(output / "adapter_config.json", config)

    behaviour_files = [
        file_identity(output / "adapter_config.json", output),
        file_identity(output / "adapter_model.safetensors", output),
    ]
    publication_digest = tree_digest(behaviour_files)
    provenance = json.loads((output / "adapter-provenance.json").read_text(encoding="utf-8"))
    provenance["adapter_digest"] = publication_digest
    write_json(output / "adapter-provenance.json", provenance)

    publication_provenance = {
        "base_model_id": EXPECTED_MODEL["base_model"]["id"],
        "base_model_revision": EXPECTED_MODEL["base_model"]["revision"],
        "publication_adapter_config_sha256": sha256_file(output / "adapter_config.json"),
        "publication_adapter_digest": publication_digest,
        "schema_version": 1,
        "source_adapter_config_sha256": source_config_sha,
        "source_adapter_digest": SOURCE_ADAPTER_DIGEST,
        "weights_sha256": sha256_file(output / "adapter_model.safetensors"),
        "weights_unchanged": sha256_file(source / "adapter_model.safetensors") == sha256_file(output / "adapter_model.safetensors"),
    }
    write_json(output / "publication-provenance.json", publication_provenance)

    card = CARD_TEMPLATE.read_text(encoding="utf-8").replace("PUBLICATION_ADAPTER_DIGEST", publication_digest)
    (output / "README.md").write_text(card, encoding="utf-8")

    verified = adapter_identity(output)
    if verified["adapter_digest"] != publication_digest or not publication_provenance["weights_unchanged"]:
        raise ValueError("packaged adapter verification failed")
    return publication_provenance


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = package(args.source, args.output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

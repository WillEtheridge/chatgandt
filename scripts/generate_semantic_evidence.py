"""Generate canonical production semantic evidence from a JSON input bundle.

The command reads one object from stdin and writes the closed evidence artifact
to stdout. It deliberately contains no path-selection or score override knobs:
all ranks, cosine scores, and token diagnostics are derived from the supplied
canonical records with the pinned MiniLM revision.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.evaluation_protocol import (  # noqa: E402
    generate_response_similarity_semantic_evidence,
    generate_stage5_semantic_evidence,
)
from chatgnt.records import ContractError, strict_json_loads  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("stage5", "response-similarity"))
    arguments = parser.parse_args()
    try:
        bundle = strict_json_loads(sys.stdin.read())
        common = {
            "artifact_id": bundle["artifact_id"],
            "verifier_identity": bundle["verifier_identity"],
            "started_at_utc": bundle["started_at_utc"],
            "verified_at_utc": bundle["verified_at_utc"],
        }
        if arguments.kind == "stage5":
            artifact = generate_stage5_semantic_evidence(
                bundle["heldout_records"], bundle["replacements"],
                bundle["source_identities"], bundle["source_records"],
                bundle["authoring_schedule_records"], bundle["candidate_attestations"],
                **common,
            )
        else:
            artifact = generate_response_similarity_semantic_evidence(
                bundle["responses"], bundle["references"], **common
            )
    except (ContractError, KeyError, OSError, TypeError, ValueError) as exc:
        print(json.dumps({"result": "fail", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(artifact, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

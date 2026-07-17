#!/usr/bin/env python3
"""Call the private ChatG&T Space without printing credentials or model text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from huggingface_hub import get_token  # noqa: E402


SPACE_ID = "wetheridge/chatgnt-api"
EXPECTED_HEALTH = {
    "baseModelRevision": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
    "adapterRevision": "12af8027a481bef7df618f32bb8787889526c343",
    "adapterDigest": "034e0c79b1201350784e0409d5f28ffcf92d8dfa9697b291b2dd4bf45129100c",
}
PROMPTS = (
    "How should I prepare for a job interview?",
    "Explain why the sky looks blue in simple terms.",
    "How can I choose which household chore to do first?",
)


def require_outcome(value: object) -> str:
    if not isinstance(value, dict) or value.get("status") not in {"valid", "failure"}:
        raise ValueError("invalid model outcome")
    if value["status"] == "valid" and not isinstance(value.get("recipe"), dict):
        raise ValueError("valid outcome has no recipe")
    if value["status"] == "failure" and value.get("failure") not in {"invalid-json", "invalid-schema"}:
        raise ValueError("invalid failure outcome")
    return str(value["status"] if value["status"] == "valid" else value["failure"])


def verify(count: int) -> dict[str, object]:
    from gradio_client import Client

    token = get_token()
    if not token:
        raise RuntimeError("Hugging Face CLI authentication is required")
    client = Client(SPACE_ID, token=token)
    health = client.predict(api_name="/health")
    if not isinstance(health, dict) or health.get("status") != "ready":
        raise ValueError("Space health check failed")
    for key, expected in EXPECTED_HEALTH.items():
        if health.get(key) != expected:
            raise ValueError(f"Space health identity mismatch: {key}")

    spirit_results = []
    tasting_results = []
    for index in range(count):
        prompt = PROMPTS[index % len(PROMPTS)]
        spirit_id = f"smoke-spirit-{uuid.uuid4()}"
        spirit = client.predict(prompt=prompt, request_id=spirit_id, api_name="/spirit_guide")
        if not isinstance(spirit, dict) or spirit.get("requestId") != spirit_id:
            raise ValueError("Spirit Guide response identity mismatch")
        spirit_results.append(require_outcome(spirit.get("outcome")))

        tasting_id = f"smoke-tasting-{uuid.uuid4()}"
        tasting = client.predict(prompt=prompt, request_id=tasting_id, api_name="/tasting_room")
        if not isinstance(tasting, dict) or tasting.get("requestId") != tasting_id:
            raise ValueError("Tasting Room response identity mismatch")
        answers = tasting.get("answers")
        if not isinstance(answers, dict) or set(answers) != {"1", "2"} or tasting.get("fineTunedAnswer") not in {1, 2}:
            raise ValueError("Tasting Room response contract mismatch")
        tasting_results.append({"1": require_outcome(answers["1"]), "2": require_outcome(answers["2"])})
    return {"spaceId": SPACE_ID, "health": "pass", "spirit": spirit_results, "tasting": tasting_results}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=3, choices=range(1, 11))
    args = parser.parse_args()
    print(json.dumps(verify(args.count), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

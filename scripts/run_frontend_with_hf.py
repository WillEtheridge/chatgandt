#!/usr/bin/env python3
"""Run the local frontend against the private Hugging Face Space safely."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

from huggingface_hub import get_token


ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
SPACE_ID = "wetheridge/chatgnt-api"


def main() -> int:
    token = get_token()
    if not token:
        raise SystemExit("Hugging Face CLI authentication is required; run `hf auth login`.")

    environment = os.environ.copy()
    environment.update(
        {
            "CHATGNT_BACKEND": "huggingface",
            "HF_SPACE_ID": SPACE_ID,
            "HF_TOKEN": token,
        }
    )
    print(f"Starting the frontend against private Space {SPACE_ID}; the token remains server-side.")
    return subprocess.run(["npm", "run", "dev"], cwd=FRONTEND, env=environment, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())

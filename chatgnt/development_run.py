"""Frozen configuration checks for the initial System A/B development run."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .configuration import PROJECT_ROOT, load_prompts, load_system_set
from .development import DEVELOPMENT_PROMPTS_V1, validate_development_prompts
from .identity import execution_order_seed, schedule_attempts, sha256_bytes
from .prompting import DEVELOPMENT_AB_SYSTEM_SET_V1, validate_development_ab_system_set
from .records import ContractError, canonical_json, read_strict_json, require_exact_keys, require_int

DEVELOPMENT_AB_RUN_PLAN_V1 = PROJECT_ROOT / "config" / "runs" / "development-ab-v1.json"
DEVELOPMENT_AB_RUN_PLAN_V1_SHA256 = "63db3e2cd65354b037c62eda2c5cabc34ae32f336b42aff8cf7f19cd08672271"
DEVELOPMENT_RUN_SEED = 20260714
DEVELOPMENT_AB_SCHEDULE_V1 = PROJECT_ROOT / "data" / "development" / "schedule-ab-v1.json"
DEVELOPMENT_AB_SCHEDULE_V1_SHA256 = "ae55b4521dfe581c10febbe0c13bcdfd26262de616a493e331c7562e89a36468"
RUN_PLAN_KEYS = {
    "primary_samples_per_system_prompt",
    "prompt_set_path",
    "run_plan_id",
    "run_seed",
    "schema_version",
    "system_set_path",
}


def validate_development_run_plan(
    path: Path = DEVELOPMENT_AB_RUN_PLAN_V1,
) -> dict[str, Any]:
    """Validate the pre-generation identities and master seed for A/B v1."""

    value, raw = read_strict_json(path)
    require_exact_keys(value, RUN_PLAN_KEYS, str(path))
    if require_int(value["schema_version"], "schema_version") != 1:
        raise ContractError(f"{path}: unsupported schema_version")
    if value["run_plan_id"] != "development-ab-v1":
        raise ContractError(f"{path}: unexpected run_plan_id")
    run_seed = require_int(value["run_seed"], "run_seed", 0, 2**64 - 1)
    if run_seed != DEVELOPMENT_RUN_SEED:
        raise ContractError(f"{path}: run_seed must equal frozen value {DEVELOPMENT_RUN_SEED}")
    if require_int(value["primary_samples_per_system_prompt"], "primary samples", 1) != 1:
        raise ContractError(f"{path}: primary sample count must equal 1")

    prompt_path = (path.parent / value["prompt_set_path"]).resolve()
    system_path = (path.parent / value["system_set_path"]).resolve()
    if prompt_path != DEVELOPMENT_PROMPTS_V1.resolve():
        raise ContractError(f"{path}: prompt_set_path does not identify frozen development v1")
    if system_path != DEVELOPMENT_AB_SYSTEM_SET_V1.resolve():
        raise ContractError(f"{path}: system_set_path does not identify frozen A/B system set v1")

    prompt_result = validate_development_prompts(prompt_path)
    system_result = validate_development_ab_system_set(system_path)
    digest = sha256_bytes(raw)
    if digest != DEVELOPMENT_AB_RUN_PLAN_V1_SHA256:
        raise ContractError(
            f"{path}: content differs from frozen development run-plan digest; "
            f"expected={DEVELOPMENT_AB_RUN_PLAN_V1_SHA256}, actual={digest}"
        )

    return {
        "result": "pass",
        "version": 1,
        "path": path.relative_to(PROJECT_ROOT).as_posix() if path.is_relative_to(PROJECT_ROOT) else str(path),
        "sha256": digest,
        "run_plan_id": value["run_plan_id"],
        "run_seed": run_seed,
        "derived_execution_order_seed": execution_order_seed(run_seed),
        "primary_samples_per_system_prompt": 1,
        "prompt_set_sha256": prompt_result["sha256"],
        "system_set_sha256": system_result["sha256"],
        "schedule_attempt_count_when_built": prompt_result["prompt_count"] * len(system_result["system_ids"]),
    }


def expected_development_schedule() -> dict[str, Any]:
    """Rebuild the exact dry-run schedule using the production scheduler."""

    run_plan = validate_development_run_plan()
    prompts, _ = load_prompts(DEVELOPMENT_PROMPTS_V1)
    systems, _ = load_system_set(DEVELOPMENT_AB_SYSTEM_SET_V1, adapter_path=None)
    attempts = schedule_attempts(
        run_plan["run_seed"],
        [prompt.prompt_id for prompt in prompts],
        [system.system_id for system in systems],
    )
    return {
        "schema_version": 1,
        "run_plan_id": run_plan["run_plan_id"],
        "run_plan_sha256": run_plan["sha256"],
        "schedule": {
            "run_seed": run_plan["run_seed"],
            "order_seed": run_plan["derived_execution_order_seed"],
            "seed_algorithm": "sha256-first-8-big-endian-v1",
            "order_algorithm": "sha256-sort-v1",
            "primary_samples_per_system_prompt": 1,
            "scheduled_attempt_count": len(attempts),
            "attempts": [attempt.to_dict() for attempt in attempts],
        },
    }


def validate_development_schedule(
    path: Path = DEVELOPMENT_AB_SCHEDULE_V1,
) -> dict[str, Any]:
    """Validate frozen order, complete A/B coverage, and paired seeds."""

    value, raw = read_strict_json(path)
    expected = expected_development_schedule()
    if canonical_json(value) != canonical_json(expected):
        raise ContractError(f"{path}: differs from the production-derived 40-attempt schedule")

    digest = sha256_bytes(raw)
    if digest != DEVELOPMENT_AB_SCHEDULE_V1_SHA256:
        raise ContractError(
            f"{path}: content differs from frozen development-schedule digest; "
            f"expected={DEVELOPMENT_AB_SCHEDULE_V1_SHA256}, actual={digest}"
        )

    attempts = value["schedule"]["attempts"]
    prompt_systems: dict[str, set[str]] = {}
    prompt_seeds: dict[str, set[int]] = {}
    system_counts = {"A": 0, "B": 0}
    for attempt in attempts:
        prompt_systems.setdefault(attempt["prompt_id"], set()).add(attempt["system_id"])
        prompt_seeds.setdefault(attempt["prompt_id"], set()).add(attempt["generation_seed"])
        system_counts[attempt["system_id"]] += 1
    if any(systems != {"A", "B"} for systems in prompt_systems.values()):
        raise ContractError(f"{path}: incomplete prompt/system pairing")
    if any(len(seeds) != 1 for seeds in prompt_seeds.values()):
        raise ContractError(f"{path}: A/B generation seeds are not paired")

    return {
        "result": "pass",
        "version": 1,
        "path": path.relative_to(PROJECT_ROOT).as_posix() if path.is_relative_to(PROJECT_ROOT) else str(path),
        "sha256": digest,
        "run_seed": value["schedule"]["run_seed"],
        "order_seed": value["schedule"]["order_seed"],
        "attempt_count": len(attempts),
        "prompt_count": len(prompt_systems),
        "system_attempt_counts": system_counts,
        "complete_ab_pair_count": sum(systems == {"A", "B"} for systems in prompt_systems.values()),
        "paired_generation_seed_count": sum(len(seeds) == 1 for seeds in prompt_seeds.values()),
        "attempt_indices_contiguous": [attempt["attempt_index"] for attempt in attempts] == list(range(len(attempts))),
        "first_five_attempts": attempts[:5],
        "production_scheduler_exact_match": True,
    }

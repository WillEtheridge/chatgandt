"""Content identity, seeds, and deterministic execution ordering."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Iterable

from .records import ScheduledAttempt, UINT64_MAX, canonical_json, require_int


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def file_identity(path: Path, relative_to: Path | None = None) -> dict[str, Any]:
    name = path.relative_to(relative_to).as_posix() if relative_to else path.name
    return {"path": name, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}


def tree_digest(files: list[dict[str, Any]]) -> str:
    ordered = sorted(files, key=lambda item: item["path"])
    return sha256_text(canonical_json(ordered))


def derive_seed(namespace: str, parts: list[Any]) -> int:
    payload = canonical_json({"namespace": namespace, "parts": parts}).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def generation_seed(run_seed: int, prompt_id: str, repeat_index: int) -> int:
    require_int(run_seed, "run_seed", 0, UINT64_MAX)
    require_int(repeat_index, "repeat_index")
    return derive_seed("generation", [run_seed, prompt_id, repeat_index])


def execution_order_seed(run_seed: int) -> int:
    require_int(run_seed, "run_seed", 0, UINT64_MAX)
    return derive_seed("execution-order", [run_seed])


def schedule_attempts(
    run_seed: int,
    prompt_ids: Iterable[str],
    system_ids: Iterable[str],
    repeat_count: int = 1,
) -> list[ScheduledAttempt]:
    require_int(repeat_count, "repeat_count", 1)
    canonical_systems = [item for item in ("A", "B", "C", "D") if item in set(system_ids)]
    order_seed = execution_order_seed(run_seed)
    keyed: list[tuple[bytes, tuple[str, str, int], str, str, int, int]] = []
    for prompt_id in prompt_ids:
        for system_id in canonical_systems:
            for repeat_index in range(repeat_count):
                seed = generation_seed(run_seed, prompt_id, repeat_index)
                payload = canonical_json({
                    "namespace": "execution-order-key",
                    "parts": [order_seed, prompt_id, system_id, repeat_index],
                }).encode("utf-8")
                keyed.append((hashlib.sha256(payload).digest(), (prompt_id, system_id, repeat_index), prompt_id, system_id, repeat_index, seed))
    keyed.sort(key=lambda item: (item[0], item[1]))
    return [
        ScheduledAttempt(index, prompt_id, system_id, repeat_index, seed)  # type: ignore[arg-type]
        for index, (_, _, prompt_id, system_id, repeat_index, seed) in enumerate(keyed)
    ]

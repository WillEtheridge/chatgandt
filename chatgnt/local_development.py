"""Local Ollama prompt-development diagnostics."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import tempfile
from typing import Any
from urllib import error, request

from .configuration import PROJECT_ROOT, load_prompt_asset, load_prompts
from .identity import generation_seed, sha256_bytes, sha256_text
from .records import ContractError, canonical_json, canonical_line, require_identifier


OLLAMA_BASE_URL = "http://127.0.0.1:11434"
LOCAL_RUN_SEED = 20260714
LOCAL_SEED_MODULUS = 2**31 - 1
LOCAL_SETTINGS = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "repeat_penalty": 1.1,
    "num_predict": 512,
    "num_ctx": 8192,
}


def local_prompt_seed(prompt_id: str, run_seed: int = LOCAL_RUN_SEED) -> int:
    """Map the formal per-prompt stream identity into Ollama's positive seed range."""

    return generation_seed(run_seed, prompt_id, 0) % LOCAL_SEED_MODULUS


def _post_json(path: str, payload: dict[str, Any], timeout: int = 900) -> dict[str, Any]:
    body = canonical_json(payload).encode("utf-8")
    api_request = request.Request(
        OLLAMA_BASE_URL + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(api_request, timeout=timeout) as response:
            value = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Ollama request failed for {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"Ollama returned a non-object for {path}")
    return value


def _get_json(path: str, timeout: int = 30) -> dict[str, Any]:
    try:
        with request.urlopen(OLLAMA_BASE_URL + path, timeout=timeout) as response:
            value = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Ollama request failed for {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"Ollama returned a non-object for {path}")
    return value


def _model_identity(model: str) -> dict[str, Any]:
    version = _get_json("/api/version")
    tags = _get_json("/api/tags").get("models")
    if not isinstance(tags, list):
        raise RuntimeError("Ollama tags response has no model list")
    tag = next((item for item in tags if isinstance(item, dict) and item.get("name") == model), None)
    if tag is None:
        raise ContractError(f"Ollama model is not installed: {model}")
    shown = _post_json("/api/show", {"model": model})
    selected_text = {
        key: shown.get(key)
        for key in ("template", "system", "parameters", "modelfile")
        if isinstance(shown.get(key), str)
    }
    return {
        "ollama_version": version.get("version"),
        "requested_model": model,
        "name": tag.get("name"),
        "digest": tag.get("digest"),
        "size": tag.get("size"),
        "modified_at": tag.get("modified_at"),
        "details": tag.get("details"),
        "capabilities": shown.get("capabilities"),
        "text_digests": {f"{key}_sha256": sha256_text(value) for key, value in selected_text.items()},
        "default_system": shown.get("system"),
    }


def _write_exclusive(path: Path, value: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(descriptor, value)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def run_local_prompt_version(
    prompt_asset_path: Path,
    prompts_path: Path,
    run_dir: Path,
    model: str = "qwen2.5:1.5b-instruct",
    run_seed: int = LOCAL_RUN_SEED,
) -> dict[str, Any]:
    """Generate one untouched Ollama response per frozen development prompt."""

    if run_dir.exists():
        raise ContractError(f"local run directory already exists: {run_dir}")
    require_identifier(run_dir.name, "run ID")
    asset = load_prompt_asset(prompt_asset_path.resolve())
    if not asset.content:
        raise ContractError("local prompt development requires a non-empty System B prompt")
    prompts, prompt_raw = load_prompts(prompts_path.resolve())
    model_identity = _model_identity(model)

    manifest = {
        "schema_version": 1,
        "kind": "ollama-prompt-development-diagnostic",
        "run_id": run_dir.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        "host": {"platform": platform.platform(), "execution": "cpu"},
        "model": model_identity,
        "prompt_asset": {
            "path": prompt_asset_path.resolve().relative_to(PROJECT_ROOT).as_posix(),
            "prompt_asset_id": asset.prompt_asset_id,
            "version": asset.version,
            "worked_example_count": asset.worked_example_count,
            "sha256": asset.source_sha256,
        },
        "prompt_set": {
            "path": prompts_path.resolve().relative_to(PROJECT_ROOT).as_posix(),
            "sha256": sha256_bytes(prompt_raw),
            "prompt_count": len(prompts),
        },
        "generation": {
            "api": "/api/chat",
            "stream": False,
            "format": None,
            "keep_alive": "5m",
            "automatic_retries": False,
            "output_repair": False,
            "run_seed": run_seed,
            "seed_algorithm": "formal-generation-seed-mod-2147483647",
            "settings": LOCAL_SETTINGS,
        },
    }

    run_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{run_dir.name}-", dir=run_dir.parent))
    try:
        _write_exclusive(temporary / "manifest.json", canonical_line(manifest))
        _write_exclusive(temporary / "prompts.jsonl", prompt_raw)
        response_path = temporary / "responses.jsonl"
        with response_path.open("xb") as handle:
            for attempt_index, prompt in enumerate(prompts):
                seed = local_prompt_seed(prompt.prompt_id, run_seed)
                messages = [
                    {"role": "system", "content": asset.content},
                    {"role": "user", "content": prompt.prompt},
                ]
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "format": None,
                    "keep_alive": "5m",
                    "options": {**LOCAL_SETTINGS, "seed": seed},
                }
                try:
                    response = _post_json("/api/chat", payload)
                    message = response.get("message")
                    raw_output = message.get("content") if isinstance(message, dict) else None
                    if not isinstance(raw_output, str):
                        raise RuntimeError("Ollama chat response has no string message content")
                    record = {
                        "schema_version": 1,
                        "run_id": run_dir.name,
                        "attempt_index": attempt_index,
                        "prompt_id": prompt.prompt_id,
                        "system_id": "B",
                        "prompt_asset_id": asset.prompt_asset_id,
                        "prompt_asset_sha256": asset.source_sha256,
                        "local_seed": seed,
                        "attempt_status": "success",
                        "raw_output": raw_output,
                        "raw_output_sha256": sha256_text(raw_output),
                        "done": response.get("done"),
                        "done_reason": response.get("done_reason"),
                        "prompt_eval_count": response.get("prompt_eval_count"),
                        "eval_count": response.get("eval_count"),
                        "total_duration_ns": response.get("total_duration"),
                        "load_duration_ns": response.get("load_duration"),
                        "prompt_eval_duration_ns": response.get("prompt_eval_duration"),
                        "eval_duration_ns": response.get("eval_duration"),
                        "error": None,
                    }
                except Exception as exc:  # preserve the failed attempt without retrying
                    record = {
                        "schema_version": 1,
                        "run_id": run_dir.name,
                        "attempt_index": attempt_index,
                        "prompt_id": prompt.prompt_id,
                        "system_id": "B",
                        "prompt_asset_id": asset.prompt_asset_id,
                        "prompt_asset_sha256": asset.source_sha256,
                        "local_seed": seed,
                        "attempt_status": "generation_error",
                        "raw_output": None,
                        "raw_output_sha256": None,
                        "done": False,
                        "done_reason": "error",
                        "prompt_eval_count": None,
                        "eval_count": None,
                        "total_duration_ns": None,
                        "load_duration_ns": None,
                        "prompt_eval_duration_ns": None,
                        "eval_duration_ns": None,
                        "error": {"type": type(exc).__name__, "message": str(exc)},
                    }
                handle.write(canonical_line(record))
                handle.flush()
                os.fsync(handle.fileno())
        temporary.rename(run_dir)
    except BaseException:
        # The uniquely named partial directory is deliberately preserved for diagnosis.
        raise

    return {
        "result": "complete",
        "run_id": run_dir.name,
        "run_dir": run_dir.resolve().relative_to(PROJECT_ROOT).as_posix(),
        "attempt_count": len(prompts),
    }

"""Device-agnostic shared inference engine and local-only runtime factories."""

from __future__ import annotations

from contextlib import contextmanager
import threading
import time
from pathlib import Path
from typing import Any, Callable, Iterator, Literal

import torch

from .configuration import EXPECTED_MODEL, ProjectConfiguration, adapter_identity
from .identity import sha256_text
from .records import ErrorInfo, GenerationProfile, GenerationRequest, GenerationResult, TimingPolicy


class InputContextExceededError(ValueError):
    pass


class OutputInvariantError(RuntimeError):
    pass


class UnexpectedTerminationError(RuntimeError):
    pass


class RuntimeVerificationError(RuntimeError):
    pass


_DEVICE_LOCKS: dict[str, threading.Lock] = {}
_DEVICE_LOCKS_GUARD = threading.Lock()


def _device_lock(device: torch.device) -> threading.Lock:
    with _DEVICE_LOCKS_GUARD:
        return _DEVICE_LOCKS.setdefault(str(device), threading.Lock())


@contextmanager
def installed_rng_state(device: torch.device, seed: int) -> Iterator[None]:
    """Install a dedicated RNG state while preserving the caller's default stream."""
    with _device_lock(device):
        generator = torch.Generator(device=device)
        generator.manual_seed(seed)
        state = generator.get_state()
        if device.type == "cuda":
            if device.index is None:
                raise RuntimeVerificationError("CUDA device must have an explicit index")
            with torch.random.fork_rng(devices=[device.index]):
                torch.cuda.set_rng_state(state, device=device)
                yield
        elif device.type == "cpu":
            with torch.random.fork_rng(devices=[]):
                torch.random.set_rng_state(state)
                yield
        else:
            raise RuntimeVerificationError(f"unsupported RNG device: {device}")


def _error_result(
    messages: tuple[dict[str, str], dict[str, str]],
    exc: BaseException,
    rendered_prompt: str | None = None,
    input_ids: tuple[int, ...] = (),
    status: Literal["input_context_exceeded", "generation_error"] = "generation_error",
) -> GenerationResult:
    return GenerationResult(
        status, messages, rendered_prompt, input_ids, len(input_ids), (), 0, 0,
        None, None, "error", None, False, None,
        ErrorInfo(exc.__class__.__name__, str(exc)),
    )


class InferenceEngine:
    """One stable base or adapted runtime exposed through the shared contract."""

    def __init__(
        self,
        model: Any,
        tokenizer: Any,
        device: str | torch.device,
        runtime_mode: Literal["base", "adapted"],
        max_context_tokens: int = 32768,
        clock: Callable[[], int] = time.perf_counter_ns,
        cuda_synchronizer: Callable[[], None] | None = None,
        rng_installer: Callable[[torch.device, int], Any] = installed_rng_state,
        runtime_evidence: dict[str, Any] | None = None,
    ) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.device = torch.device(device)
        self.runtime_mode = runtime_mode
        self.max_context_tokens = max_context_tokens
        self.clock = clock
        self.cuda_synchronizer = cuda_synchronizer
        self.rng_installer = rng_installer
        self.runtime_evidence = runtime_evidence or {}
        self.last_failure_fatal = False
        self.last_failure_phase: str | None = None

    def _fail(
        self, messages: tuple[dict[str, str], dict[str, str]], exc: BaseException,
        phase: str, fatal: bool, rendered: str | None = None, input_ids: tuple[int, ...] = (),
        status: Literal["input_context_exceeded", "generation_error"] = "generation_error",
    ) -> GenerationResult:
        self.last_failure_fatal = fatal
        self.last_failure_phase = phase
        return _error_result(messages, exc, rendered, input_ids, status)

    def generate(
        self,
        request: GenerationRequest,
        profile: GenerationProfile,
        timing: TimingPolicy,
    ) -> GenerationResult:
        self.last_failure_fatal = False
        self.last_failure_phase = None
        expects_adapter = self.runtime_mode == "adapted"
        if request.adapter_enabled != expects_adapter:
            raise ValueError(f"{self.runtime_mode} engine refuses adapter_enabled={request.adapter_enabled}")
        if timing.canonical and (self.device.type != "cuda" or not timing.enabled or not timing.synchronize_cuda):
            raise ValueError("canonical timing requires synchronized CUDA")
        messages = (
            {"role": "system", "content": request.system_content},
            {"role": "user", "content": request.user_prompt},
        )
        try:
            rendered = self.tokenizer.apply_chat_template(
                list(messages), tokenize=False, add_generation_prompt=True
            )
        except Exception as exc:
            return self._fail(messages, exc, "rendering", True)
        try:
            encoded = self.tokenizer(
                rendered, add_special_tokens=False, truncation=False, return_tensors="pt"
            )
            ids_tensor = encoded["input_ids"]
            if not isinstance(ids_tensor, torch.Tensor) or ids_tensor.ndim != 2 or ids_tensor.shape[0] != 1:
                raise OutputInvariantError("tokenizer input_ids must have shape [1, sequence_length]")
            if ids_tensor.dtype not in (torch.int8, torch.int16, torch.int32, torch.int64, torch.uint8):
                raise OutputInvariantError("tokenizer input_ids must have integer dtype")
            input_ids = tuple(int(item) for item in ids_tensor[0].tolist())
            attention = encoded.get("attention_mask")
            if attention is None:
                attention = torch.ones_like(ids_tensor)
            if not isinstance(attention, torch.Tensor) or attention.shape != ids_tensor.shape or not torch.all(attention == 1):
                raise OutputInvariantError("batch-one unpadded attention mask must be all ones and match input shape")
        except Exception as exc:
            return self._fail(messages, exc, "tokenization", True, rendered)
        if len(input_ids) + profile.max_new_tokens > self.max_context_tokens:
            exc = InputContextExceededError(
                f"input_token_count ({len(input_ids)}) + max_new_tokens ({profile.max_new_tokens}) exceeds max_context_tokens ({self.max_context_tokens})"
            )
            return self._fail(messages, exc, "context", False, rendered, input_ids, "input_context_exceeded")
        try:
            model_inputs = {
                "input_ids": ids_tensor.to(self.device),
                "attention_mask": attention.to(self.device),
            }
        except Exception as exc:
            return self._fail(messages, exc, "device-transfer", True, rendered, input_ids)

        kwargs = profile.generation_kwargs()
        duration: int | None = None
        output: Any = None
        try:
            self.model.eval()
            with self.rng_installer(self.device, request.generation_seed):
                with torch.inference_mode():
                    if timing.enabled:
                        if timing.synchronize_cuda:
                            if self.cuda_synchronizer is None:
                                raise RuntimeVerificationError("CUDA synchronizer is required")
                            self.cuda_synchronizer()
                        started = self.clock()
                    try:
                        output = self.model.generate(**model_inputs, **kwargs)
                    except Exception as exc:
                        fatal = isinstance(exc, RuntimeError)
                        return self._fail(messages, exc, "generation", fatal, rendered, input_ids)
                    if timing.enabled:
                        if timing.synchronize_cuda:
                            assert self.cuda_synchronizer is not None
                            self.cuda_synchronizer()
                        duration = self.clock() - started
        except Exception as exc:
            phase = "rng-or-synchronization"
            return self._fail(messages, exc, phase, True, rendered, input_ids)

        try:
            if not isinstance(output, torch.Tensor):
                raise OutputInvariantError("generate output must be a tensor")
            if output.ndim != 2 or output.shape[0] != 1:
                raise OutputInvariantError("generate output must have shape [1, sequence_length]")
            if output.dtype not in (torch.int8, torch.int16, torch.int32, torch.int64, torch.uint8):
                raise OutputInvariantError("generate output must have integer dtype")
            output_cpu = output.detach().cpu()
            if output_cpu.shape[1] < len(input_ids):
                raise OutputInvariantError("generate output is shorter than input")
            expected_prefix = torch.tensor(input_ids, dtype=output_cpu.dtype)
            if not torch.equal(output_cpu[0, :len(input_ids)], expected_prefix):
                raise OutputInvariantError("generate output prefix does not equal input IDs")
            generated = tuple(int(item) for item in output_cpu[0, len(input_ids):].tolist())
            reached_max = len(generated) == profile.max_new_tokens
            if generated and generated[-1] in profile.eos_token_ids:
                termination = "eos_token"; terminal = generated[-1]
            elif reached_max:
                termination = "max_new_tokens"; terminal = None
            else:
                raise UnexpectedTerminationError(
                    "generation stopped without EOS before max_new_tokens"
                )
            raw_output = self.tokenizer.decode(
                list(generated), skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )
            visible = sum(token_id not in set(self.tokenizer.all_special_ids) for token_id in generated)
        except Exception as exc:
            return self._fail(messages, exc, "postprocessing", True, rendered, input_ids)
        return GenerationResult(
            "success", messages, rendered, input_ids, len(input_ids), generated,
            len(generated), visible, raw_output, sha256_text(raw_output), termination,
            terminal, reached_max, duration, None,
        )


def _attention_impl(model: Any) -> str | None:
    config = getattr(model, "config", None)
    return getattr(config, "_attn_implementation", getattr(config, "attn_implementation", None))


def _verify_placement(model: Any, device: torch.device) -> None:
    expected = str(device)
    for name, tensor in list(model.named_parameters()) + list(model.named_buffers()):
        if str(tensor.device) != expected:
            raise RuntimeVerificationError(f"tensor {name} is on {tensor.device}, expected {expected}")
    device_map = getattr(model, "hf_device_map", None)
    if device_map is not None and any(str(value) not in (expected, str(device.index)) for value in device_map.values()):
        raise RuntimeVerificationError("hf_device_map does not match requested device")


def _base_parameter_count(model: Any) -> int:
    return sum(parameter.numel() for name, parameter in model.named_parameters() if "lora_" not in name)


def load_engine(
    snapshot_path: Path,
    device: str,
    runtime_mode: Literal["base", "adapted"],
    project: ProjectConfiguration,
    adapter_path: Path | None = None,
    allow_unprovenanced_diagnostic_adapter: bool = False,
    formal_cuda: bool = True,
) -> InferenceEngine:
    """Load and validate one stable runtime without any network fallback."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    exact_device = torch.device(device)
    if formal_cuda and (exact_device.type != "cuda" or exact_device.index is None):
        raise RuntimeVerificationError("formal runtime requires explicit cuda:N")
    tokenizer = AutoTokenizer.from_pretrained(snapshot_path, local_files_only=True)
    if tokenizer.__class__.__name__ != "Qwen2Tokenizer" or len(tokenizer) != 151665:
        raise RuntimeVerificationError("tokenizer class or length mismatch")
    if tokenizer.eos_token_id != 151645:
        raise RuntimeVerificationError("tokenizer EOS identity mismatch")
    if sha256_text(tokenizer.chat_template) != project.model.values["tokenizer"]["chat_template_sha256"]:
        raise RuntimeVerificationError("chat template digest mismatch")

    load_kwargs: dict[str, Any] = {
        "local_files_only": True, "dtype": torch.bfloat16,
        "low_cpu_mem_usage": True, "attn_implementation": "sdpa",
    }
    if exact_device.type == "cuda":
        load_kwargs["device_map"] = {"": exact_device}
    model = AutoModelForCausalLM.from_pretrained(snapshot_path, **load_kwargs)
    if exact_device.type == "cpu":
        model.to(exact_device)
    if model.__class__.__name__ != "Qwen2ForCausalLM" or getattr(model.config, "model_type", None) != "qwen2":
        raise RuntimeVerificationError("model architecture mismatch")
    if getattr(model.config, "max_position_embeddings", None) != 32768:
        raise RuntimeVerificationError("model context limit mismatch")
    base_count = sum(parameter.numel() for parameter in model.parameters())
    if base_count != EXPECTED_MODEL["base_model"]["parameter_count"]:
        raise RuntimeVerificationError("base parameter count mismatch")
    dtypes = sorted({str(parameter.dtype) for parameter in model.parameters() if parameter.is_floating_point()})
    if dtypes != ["torch.bfloat16"]:
        raise RuntimeVerificationError(f"base dtype mismatch: {dtypes}")
    if _attention_impl(model) != "sdpa":
        raise RuntimeVerificationError("effective attention implementation is not sdpa")
    controlled = project.primary_profile.generation_kwargs()
    effective = model.generation_config.to_dict()
    for key, expected in controlled.items():
        if key in effective and effective[key] is not None and effective[key] != expected:
            raise RuntimeVerificationError(f"model generation configuration conflicts with {key}")
    _verify_placement(model, exact_device)

    adapter_evidence = None
    if runtime_mode == "adapted":
        if adapter_path is None:
            raise RuntimeVerificationError("adapted runtime requires adapter path")
        adapter_evidence = adapter_identity(adapter_path, allow_unprovenanced_diagnostic_adapter)
        from peft import PeftModel
        model = PeftModel.from_pretrained(
            model, adapter_path, adapter_name="chatgnt", is_trainable=False,
            autocast_adapter_dtype=True, ephemeral_gpu_offload=False,
            low_cpu_mem_usage=False,
        )
        active = sorted(model.active_adapters)
        if active != ["chatgnt"]:
            raise RuntimeVerificationError(f"active adapter mismatch: {active}")
        if any(parameter.requires_grad for parameter in model.parameters()):
            raise RuntimeVerificationError("adapted runtime contains trainable parameters")
        if _base_parameter_count(model) != base_count:
            raise RuntimeVerificationError("adapted base-only parameter count mismatch")
        from peft.tuners.tuners_utils import BaseTunerLayer
        for module in model.modules():
            if isinstance(module, BaseTunerLayer) and getattr(module, "merged_adapters", []):
                raise RuntimeVerificationError("adapter is merged")
        _verify_placement(model, exact_device)
        adapter_evidence.update({
            "active_adapters": active,
            "trainable_parameter_count": sum(p.numel() for p in model.parameters() if p.requires_grad),
            "parameter_dtypes": sorted({str(p.dtype) for n, p in model.named_parameters() if "lora_" in n}),
            "merged": False,
        })
    elif adapter_path is not None:
        raise RuntimeVerificationError("base runtime forbids adapter path")
    model.eval()
    evidence = {
        "parameter_count": base_count, "base_dtypes": dtypes,
        "attention_implementation": _attention_impl(model), "adapter": adapter_evidence,
        "effective_generation_config": model.generation_config.to_dict(),
        "device": str(exact_device),
    }
    synchronizer = (lambda: torch.cuda.synchronize(exact_device)) if exact_device.type == "cuda" else None
    return InferenceEngine(model, tokenizer, exact_device, runtime_mode,
        project.model.values["base_model"]["max_context_tokens"],
        cuda_synchronizer=synchronizer, runtime_evidence=evidence)


def cuda_health_probe(device: torch.device) -> None:
    left = torch.ones(1, device=device)
    right = torch.ones(1, device=device)
    result = left + right
    if result.item() != 2:
        raise RuntimeVerificationError("CUDA health probe produced an invalid result")
    torch.cuda.synchronize(device)

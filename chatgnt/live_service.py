"""Small live-serving boundary built on the frozen inference and validation code."""

from __future__ import annotations

import logging
import secrets
from typing import Any

from .configuration import ProjectConfiguration, PromptAsset
from .records import GenerationRequest, strict_json_loads
from .validation import LoadedResponseSchema, validate_response


LOGGER = logging.getLogger("chatgnt.live")
MAX_PROMPT_CHARACTERS = 500


class LiveContractError(ValueError):
    pass


class LiveGenerationError(RuntimeError):
    pass


class LiveService:
    """Serve Systems B and C without changing the experimental generation contract."""

    def __init__(
        self,
        base_engine: Any,
        adapted_engine: Any,
        project: ProjectConfiguration,
        five_shot_asset: PromptAsset,
        minimal_asset: PromptAsset,
        response_schema: LoadedResponseSchema,
        *,
        adapter_revision: str,
        adapter_digest: str,
    ) -> None:
        self.base_engine = base_engine
        self.adapted_engine = adapted_engine
        self.project = project
        self.five_shot_asset = five_shot_asset
        self.minimal_asset = minimal_asset
        self.response_schema = response_schema
        self.adapter_revision = adapter_revision
        self.adapter_digest = adapter_digest

    @staticmethod
    def _prompt(value: str) -> str:
        if not isinstance(value, str):
            raise LiveContractError("prompt must be a string")
        prompt = value.strip()
        if not prompt:
            raise LiveContractError("prompt must not be empty")
        if len(prompt) > MAX_PROMPT_CHARACTERS:
            raise LiveContractError(f"prompt must be {MAX_PROMPT_CHARACTERS} characters or fewer")
        return prompt

    @staticmethod
    def _request_id(value: str) -> str:
        from .records import IDENTIFIER_RE

        if not isinstance(value, str) or IDENTIFIER_RE.fullmatch(value) is None:
            raise LiveContractError("request_id must be a valid identifier")
        return value

    def _generate(self, prompt: str, request_id: str, system_id: str, seed: int) -> dict[str, Any]:
        if system_id == "B":
            engine = self.base_engine
            asset = self.five_shot_asset
            adapter_enabled = False
        elif system_id == "C":
            engine = self.adapted_engine
            asset = self.minimal_asset
            adapter_enabled = True
        else:
            raise ValueError("live service supports only Systems B and C")
        request = GenerationRequest(
            prompt_id=request_id,
            user_prompt=prompt,
            system_id=system_id,  # type: ignore[arg-type]
            prompt_asset_id=asset.prompt_asset_id,
            prompt_asset_sha256=asset.source_sha256,
            system_content=asset.content,
            adapter_enabled=adapter_enabled,
            repeat_index=0,
            generation_seed=seed,
        )
        result = engine.generate(request, self.project.primary_profile, self.project.timing_policy)
        if result.attempt_status != "success" or result.raw_output is None:
            LOGGER.warning("generation_failed request_id=%s system=%s status=%s", request_id, system_id, result.attempt_status)
            raise LiveGenerationError(f"System {system_id} generation failed")
        validation = validate_response(result.raw_output, self.response_schema)
        if not validation["json_valid"]:
            outcome: dict[str, Any] = {"status": "failure", "failure": "invalid-json"}
        elif not validation["schema_valid"]:
            outcome = {"status": "failure", "failure": "invalid-schema"}
        else:
            recipe = strict_json_loads(result.raw_output)
            outcome = {"status": "valid", "recipe": recipe}
        LOGGER.info(
            "generation_complete request_id=%s system=%s outcome=%s input_tokens=%s output_tokens=%s generation_ms=%s",
            request_id,
            system_id,
            outcome["status"] if outcome["status"] == "valid" else outcome["failure"],
            result.input_token_count,
            result.generated_token_count,
            round(result.generation_duration_ns / 1_000_000, 2) if result.generation_duration_ns is not None else None,
        )
        return outcome

    def spirit_guide(self, prompt: str, request_id: str) -> dict[str, Any]:
        clean_prompt = self._prompt(prompt)
        clean_request_id = self._request_id(request_id)
        return {
            "schemaVersion": 1,
            "requestId": clean_request_id,
            "outcome": self._generate(clean_prompt, clean_request_id, "C", secrets.randbits(64)),
        }

    def tasting_room(self, prompt: str, request_id: str) -> dict[str, Any]:
        clean_prompt = self._prompt(prompt)
        clean_request_id = self._request_id(request_id)
        seed = secrets.randbits(64)
        prompted = self._generate(clean_prompt, clean_request_id, "B", seed)
        adapted = self._generate(clean_prompt, clean_request_id, "C", seed)
        fine_tuned_answer = 1 if secrets.randbelow(2) == 0 else 2
        answers = {"1": adapted, "2": prompted} if fine_tuned_answer == 1 else {"1": prompted, "2": adapted}
        return {
            "schemaVersion": 1,
            "requestId": clean_request_id,
            "answers": answers,
            "fineTunedAnswer": fine_tuned_answer,
        }

    def health(self) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "status": "ready",
            "baseModelId": self.project.model.values["base_model"]["id"],
            "baseModelRevision": self.project.model.values["base_model"]["revision"],
            "adapterRevision": self.adapter_revision,
            "adapterDigest": self.adapter_digest,
            "responseSchemaSha256": self.response_schema.sha256,
        }

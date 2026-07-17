from __future__ import annotations

import logging
from pathlib import Path

import gradio as gr
from huggingface_hub import snapshot_download
import spaces

from chatgnt.configuration import adapter_identity, load_project_configuration, load_prompt_asset, verify_model_files
from chatgnt.inference import load_engine
from chatgnt.live_service import LiveService
from chatgnt.validation import load_response_schema


BASE_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
BASE_MODEL_REVISION = "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
ADAPTER_ID = "wetheridge/chatgnt-qwen2.5-1.5b-lora"
ADAPTER_REVISION = "12af8027a481bef7df618f32bb8787889526c343"
ADAPTER_DIGEST = "034e0c79b1201350784e0409d5f28ffcf92d8dfa9697b291b2dd4bf45129100c"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
root = Path(__file__).resolve().parent
base_snapshot = Path(snapshot_download(BASE_MODEL_ID, revision=BASE_MODEL_REVISION, local_files_only=True))
adapter_snapshot = Path(snapshot_download(ADAPTER_ID, revision=ADAPTER_REVISION, local_files_only=True))
verify_model_files(base_snapshot, root / "config/model-files.json")
adapter_evidence = adapter_identity(adapter_snapshot)
if adapter_evidence["adapter_digest"] != ADAPTER_DIGEST:
    raise RuntimeError("published adapter digest mismatch")

project = load_project_configuration(root / "config")
base_engine = load_engine(base_snapshot, "cuda:0", "base", project)
adapted_engine = load_engine(base_snapshot, "cuda:0", "adapted", project, adapter_path=adapter_snapshot)
service = LiveService(
    base_engine,
    adapted_engine,
    project,
    load_prompt_asset(root / "config/prompts/five-shot-v3.json"),
    load_prompt_asset(root / "config/prompts/minimal-v1.json"),
    load_response_schema(root / "schemas/chatgnt-response-v1.schema.json"),
    adapter_revision=ADAPTER_REVISION,
    adapter_digest=ADAPTER_DIGEST,
)


@spaces.GPU(duration=60)
def spirit_guide(prompt: str, request_id: str):
    return service.spirit_guide(prompt, request_id)


@spaces.GPU(duration=120)
def tasting_room(prompt: str, request_id: str):
    return service.tasting_room(prompt, request_id)


def health():
    return service.health()


with gr.Blocks(title="ChatG&T Inference API") as demo:
    gr.Markdown("# ChatG&T Inference API\nPrivate structured-generation backend for the ChatG&T portfolio experiment.")
    with gr.Tab("Spirit Guide"):
        spirit_prompt = gr.Textbox(label="Prompt", lines=3, max_lines=8)
        spirit_request_id = gr.Textbox(label="Request ID")
        spirit_output = gr.JSON(label="Outcome")
        gr.Button("Generate").click(
            spirit_guide,
            inputs=[spirit_prompt, spirit_request_id],
            outputs=spirit_output,
            api_name="spirit_guide",
        )
    with gr.Tab("Tasting Room"):
        tasting_prompt = gr.Textbox(label="Prompt", lines=3, max_lines=8)
        tasting_request_id = gr.Textbox(label="Request ID")
        tasting_output = gr.JSON(label="Comparison")
        gr.Button("Generate pair").click(
            tasting_room,
            inputs=[tasting_prompt, tasting_request_id],
            outputs=tasting_output,
            api_name="tasting_room",
        )
    with gr.Tab("Health"):
        health_output = gr.JSON(label="Runtime identity")
        gr.Button("Check").click(health, inputs=[], outputs=health_output, api_name="health", queue=False)

demo.queue(default_concurrency_limit=1, max_size=20).launch(ssr_mode=False)

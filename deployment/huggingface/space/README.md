---
title: ChatG&T Inference API
emoji: 🍸
colorFrom: gray
colorTo: yellow
sdk: gradio
sdk_version: 6.20.0
app_file: app.py
python_version: 3.12.12
pinned: false
private: true
startup_duration_timeout: 1h
models:
- Qwen/Qwen2.5-1.5B-Instruct
- wetheridge/chatgnt-qwen2.5-1.5b-lora
tags:
- structured-generation
- lora
- zerogpu
preload_from_hub:
- Qwen/Qwen2.5-1.5B-Instruct config.json,generation_config.json,merges.txt,model.safetensors,tokenizer.json,tokenizer_config.json,vocab.json 989aa7980e4cf806f80c7fef2b1adb7bc71aa306
- wetheridge/chatgnt-qwen2.5-1.5b-lora adapter_config.json,adapter_model.safetensors,adapter-provenance.json,publication-provenance.json 12af8027a481bef7df618f32bb8787889526c343
---

# ChatG&T private inference API

This private Gradio Space serves the ChatG&T portfolio site's Spirit Guide and Tasting Room through named API endpoints.

The evaluated project environment used PyTorch 2.12.1. This Space uses PyTorch 2.11.0 because it is the newest version currently accepted by ZeroGPU; all model, adapter, prompt, generation, and validation identities remain pinned.

- `/spirit_guide` runs the evaluated LoRA adapter with the minimal prompt.
- `/tasting_room` compares the prompted base model with the adapted model using a matched sampling seed.
- `/health` reports immutable model, adapter, and schema identity without allocating a GPU.

Model-format failures are returned honestly. The service does not retry, repair, or reformat generated output, and it does not persist prompts, responses, or visitor choices.

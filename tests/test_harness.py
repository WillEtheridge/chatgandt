import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import torch

from chatgnt.configuration import PROJECT_ROOT, Prompt, PromptAsset, SystemDefinition, load_project_configuration
from chatgnt.harness import RuntimeAbort, _make_manifest, _publish, execute_run, inspect_run
from chatgnt.identity import execution_order_seed, file_identity, schedule_attempts, sha256_bytes, sha256_text, tree_digest
from chatgnt.records import ErrorInfo, GenerationResult, canonical_line


def prompt_bytes():
    return canonical_line({"prompt_id": "p1", "prompt": "hello", "metadata": {}})


def manifest(frozen: bytes):
    attempt = schedule_attempts(1, ["p1"], ["A"])[0].to_dict()
    implementation_files = [file_identity(path, PROJECT_ROOT) for path in sorted((PROJECT_ROOT/"chatgnt").glob("*.py")) if path.is_file()]
    digest = tree_digest(implementation_files)
    return {
        "schema_version": 1, "specification_version": "1.2", "run_id": "run-1",
        "created_at_utc": "2026-07-14T12:00:00.000000+00:00", "diagnostic": None,
        "implementation": {"package_version": "0.1.0", "behaviour_files": implementation_files, "behaviour_digest": digest,
            "pyproject_sha256": "0"*64, "uv_lock_sha256": "1"*64, "git_commit": None, "git_dirty": None},
        "prompt_set": {"source_path": "source.jsonl", "source_sha256": "2"*64,
            "frozen_sha256": sha256_bytes(frozen), "prompt_count": 1, "prompt_ids": ["p1"]},
        "system_set": {"source_path": "systems.json", "source_sha256": "3"*64, "systems": [{
            "system_id": "A", "adapter_enabled": False, "prompt_asset": {"source_path": "minimal.json",
                "source_sha256": "4"*64, "schema_version": 1, "prompt_asset_id": "minimal",
                "version": "1", "worked_example_count": 0, "content": ""}}]},
        "schedule": {"run_seed": 1, "order_seed": execution_order_seed(1), "seed_algorithm": "sha256-first-8-big-endian-v1",
            "order_algorithm": "sha256-sort-v1", "primary_samples_per_system_prompt": 1,
            "scheduled_attempt_count": 1, "attempts": [attempt]},
        "model": {"model_id": "m", "revision": "r", "snapshot_path": "snapshot", "architecture": "a",
            "model_type": "qwen2", "parameter_count": 1, "dtype": "bfloat16", "max_context_tokens": 32768,
            "weights_sha256": "5"*64, "behaviour_files": [], "effective_generation_config": {}},
        "tokenizer": {"class": "Qwen2Tokenizer", "length": 151665, "chat_template_sha256": "6"*64,
            "eos_token_id": 99, "generation_eos_token_ids": [99,98], "pad_token_id": 98,
            "all_special_ids": [98,99]},
        "adapter": None,
        "configuration": {key: {"source_path": f"config/{key}.toml", "source_sha256": "7"*64,
            "values": ({"primary": {"max_new_tokens": 2}} if key == "generation" else {})}
            for key in ("model","generation","inference")},
        "environment": {"python":"3.12","platform":"x","torch":"x","transformers":"x","peft":"x",
            "tokenizers":"x","safetensors":"x","accelerate":"x","torch_cuda_build":"13.0",
            "cuda_driver":None,"cudnn":1,"device":"cuda:0","device_name":"fake",
            "device_total_memory_bytes":1,"bf16_supported":True,"attention_implementation":"sdpa",
            "collection_errors":[]},
        "timing": {"metric":"synchronized-model-generate","clock":"time.perf_counter_ns","cuda_synchronize":True,
            "include_prompt_prefill":True,"include_output_generation":True,"include_tokenization":False,
            "include_model_loading":False,"batch_size":1,"reusable_conversation_cache":False},
        "warmup": {"per_loaded_runtime":1,"profile":{},"timed":False,"base_runtime_performed":True,
            "adapted_runtime_performed":False},
    }


def success_record():
    seed = schedule_attempts(1, ["p1"], ["A"])[0].generation_seed
    return {"schema_version":1,"run_id":"run-1","attempt_index":0,"prompt_id":"p1","system_id":"A",
        "repeat_index":0,"generation_seed":seed,"attempt_status":"success","adapter_enabled":False,
        "prompt_asset_id":"minimal","prompt_asset_sha256":"4"*64,
        "messages":[{"role":"system","content":""},{"role":"user","content":"hello"}],
        "rendered_prompt":"rendered","input_token_ids":[1,2],"input_token_count":2,
        "generated_token_ids":[7,99],"generated_token_count":2,"visible_output_token_count":1,
        "raw_output":"value","raw_output_sha256":sha256_text("value"),"termination_reason":"eos_token",
        "terminal_token_id":99,"reached_max_new_tokens":True,"generation_duration_ns":5,"error":None}


def create_run(root: Path, records):
    root.mkdir(); frozen=prompt_bytes()
    (root/"manifest.json").write_bytes(canonical_line(manifest(frozen)))
    (root/"prompts.jsonl").write_bytes(frozen)
    (root/"responses.jsonl").write_bytes(b"".join(records))


class PublicationTests(unittest.TestCase):
    def test_exclusive_three_file_publication_and_refusal_to_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            run=Path(td)/"run"; frozen=prompt_bytes(); m=manifest(frozen)
            handle=_publish(run,m,frozen); handle.close()
            self.assertEqual(sorted(x.name for x in run.iterdir()), ["manifest.json","prompts.jsonl","responses.jsonl"])
            before={x.name:x.read_bytes() for x in run.iterdir()}
            with self.assertRaises(FileExistsError): _publish(run,m,frozen)
            self.assertEqual(before,{x.name:x.read_bytes() for x in run.iterdir()})

    def test_manifest_builder_produces_canonical_json_values(self):
        class Qwen2Tokenizer:
            eos_token_id=151645; all_special_ids=[151643,151645]; chat_template="template"
            def __len__(self): return 151665
        environment={"python":"3.12","platform":"x","torch":"x","transformers":"x","peft":"x",
            "tokenizers":"x","safetensors":"x","accelerate":"x","torch_cuda_build":"13.0",
            "cuda_driver":None,"cudnn":1,"device":"cuda:0","device_name":"fake",
            "device_total_memory_bytes":1,"bf16_supported":True,"attention_implementation":"sdpa",
            "collection_errors":[]}
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); source=root/"minimal.json"; source.write_text("{}")
            asset=PromptAsset(source,"4"*64,1,"minimal","1",0,"")
            systems=[SystemDefinition("A",False,asset)]; prompts=[Prompt("p1","hello",{})]
            frozen=prompt_bytes(); schedule=schedule_attempts(1,["p1"],["A"])
            engine=SimpleNamespace(tokenizer=Qwen2Tokenizer(),device=SimpleNamespace(),runtime_evidence={
                "parameter_count":1543714304,"attention_implementation":"sdpa",
                "effective_generation_config":{},"adapter":None})
            project=load_project_configuration()
            with patch("chatgnt.harness._environment",return_value=environment):
                value=_make_manifest("run-1",root/"prompts.jsonl",b"source",prompts,frozen,
                    root/"systems.json",b"systems",systems,schedule,project,[],root/"snapshot",
                    {"base":engine},None,None)
            value["schedule"]["run_seed"]=1; value["schedule"]["order_seed"]=execution_order_seed(1)
            self.assertTrue(canonical_line(value).endswith(b"\n"))


class RunnerTests(unittest.TestCase):
    class Qwen2Tokenizer:
        eos_token_id=151645; all_special_ids=[151643,151645]; chat_template="template"
        def __len__(self): return 151665

    class Engine:
        def __init__(self, fail=False):
            self.tokenizer=RunnerTests.Qwen2Tokenizer(); self.device=torch.device("cuda:0")
            self.last_failure_fatal=False; self.calls=[]; self.fail=fail
            self.runtime_evidence={"parameter_count":1543714304,"base_dtypes":["torch.bfloat16"],
                "attention_implementation":"sdpa","effective_generation_config":{},"adapter":None}
        def generate(self, request, profile, timing):
            self.calls.append((request.system_id,timing.enabled))
            messages=({"role":"system","content":request.system_content},{"role":"user","content":request.user_prompt})
            if self.fail and request.prompt_id != "warmup":
                self.last_failure_fatal=True
                return GenerationResult("generation_error",messages,"rendered",(1,),1,(),0,0,None,None,
                    "error",None,False,None,ErrorInfo("RuntimeError","fatal"))
            return GenerationResult("success",messages,"rendered",(1,),1,(7,151645),2,1,"out",
                sha256_text("out"),"eos_token",151645,False,1,None)

    @staticmethod
    def environment():
        return {"python":"3.12","platform":"x","torch":"x","transformers":"x","peft":"x",
            "tokenizers":"x","safetensors":"x","accelerate":"x","torch_cuda_build":"13.0",
            "cuda_driver":None,"cudnn":1,"device":"cuda:0","device_name":"fake",
            "device_total_memory_bytes":1,"bf16_supported":True,"attention_implementation":"sdpa",
            "collection_errors":[]}

    def inputs(self, root: Path, count=1):
        (root/"minimal.json").write_bytes(canonical_line({"schema_version":1,"prompt_asset_id":"minimal","version":"1","worked_example_count":0,"content":""}))
        (root/"five.json").write_bytes(canonical_line({"schema_version":1,"prompt_asset_id":"five","version":"1","worked_example_count":5,"content":"five examples"}))
        (root/"prompts.jsonl").write_bytes(b"".join(canonical_line({"prompt_id":f"p{i}","prompt":"hello","metadata":{}}) for i in range(count)))
        (root/"systems.json").write_bytes(canonical_line({"schema_version":1,"systems":[
            {"system_id":"A","prompt_asset_path":"minimal.json","adapter_enabled":False},
            {"system_id":"B","prompt_asset_path":"five.json","adapter_enabled":False}]}))

    def test_complete_and_fatal_partial_runs_use_three_artefacts(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self.inputs(root); runs=root/"runs"; engine=self.Engine()
            with patch("chatgnt.harness._verify_device",return_value=torch.device("cuda:0")), \
                 patch("chatgnt.harness.verify_model_files",return_value=[]), \
                 patch("chatgnt.harness.load_engine",return_value=engine), \
                 patch("chatgnt.harness._environment",return_value=self.environment()):
                code, run_dir, report=execute_run(root/"prompts.jsonl",root/"systems.json",1,"cuda:0",
                    run_id="complete",runs_root=runs)
            self.assertEqual(code,0); self.assertTrue(report["complete"])
            self.assertEqual(sorted(path.name for path in run_dir.iterdir()),["manifest.json","prompts.jsonl","responses.jsonl"])
            immutable={name:(run_dir/name).read_bytes() for name in ("manifest.json","prompts.jsonl")}
            self.assertEqual(immutable,{name:(run_dir/name).read_bytes() for name in immutable})

            self.inputs(root,count=2); fatal=self.Engine(fail=True)
            with patch("chatgnt.harness._verify_device",return_value=torch.device("cuda:0")), \
                 patch("chatgnt.harness.verify_model_files",return_value=[]), \
                 patch("chatgnt.harness.load_engine",return_value=fatal), \
                 patch("chatgnt.harness._environment",return_value=self.environment()):
                with self.assertRaises(RuntimeAbort):
                    execute_run(root/"prompts.jsonl",root/"systems.json",1,"cuda:0",
                        run_id="partial",runs_root=runs)
            partial=inspect_run(runs/"partial")
            self.assertFalse(partial["complete"]); self.assertEqual(partial["response_line_count"],1)


class InspectorTests(unittest.TestCase):
    def test_complete_run(self):
        with tempfile.TemporaryDirectory() as td:
            run=Path(td)/"run"; create_run(run,[canonical_line(success_record())])
            report=inspect_run(run)
            self.assertTrue(report["complete"]); self.assertEqual(report["valid_response_count"],1)

    def test_partial_duplicate_malformed_and_corruption(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            partial=base/"partial"; create_run(partial,[])
            self.assertEqual(inspect_run(partial)["missing_attempt_indices"],[0])
            duplicate=base/"duplicate"; line=canonical_line(success_record()); create_run(duplicate,[line,line])
            self.assertEqual(inspect_run(duplicate)["duplicate_attempt_indices"],[0])
            malformed=base/"malformed"; create_run(malformed,[line[:-1]])
            self.assertEqual(inspect_run(malformed)["malformed_line_numbers"],[1])
            corrupt=base/"corrupt"; record=success_record(); record["raw_output_sha256"]="0"*64
            create_run(corrupt,[canonical_line(record)])
            self.assertFalse(inspect_run(corrupt)["complete"])

    def test_noncanonical_manifest_and_implementation_digest_detected(self):
        with tempfile.TemporaryDirectory() as td:
            run=Path(td)/"run"; create_run(run,[canonical_line(success_record())])
            value=manifest(prompt_bytes()); value["implementation"]["behaviour_digest"]="0"*64
            (run/"manifest.json").write_bytes(canonical_line(value))
            self.assertTrue(inspect_run(run)["integrity_errors"])

    def test_missing_directory_exact_report_shape(self):
        with tempfile.TemporaryDirectory() as td:
            report=inspect_run(Path(td)/"absent")
            self.assertEqual(set(report), {"schema_version","run_id","scheduled_count","response_line_count",
                "valid_response_count","unique_recorded_attempt_count","missing_attempt_indices",
                "duplicate_attempt_indices","unexpected_attempt_indices","malformed_line_numbers",
                "integrity_errors","complete"})
            self.assertIsNone(report["run_id"])


if __name__ == "__main__": unittest.main()

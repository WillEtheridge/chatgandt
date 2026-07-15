import copy
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import torch

from chatgnt.configuration import CONFIG_ROOT, PROJECT_ROOT, Prompt, PromptAsset, SystemDefinition, load_project_configuration
from chatgnt.harness import RuntimeAbort, _diagnostic_declaration, _environment, _make_manifest, _publish, execute_run, inspect_run
from chatgnt.identity import execution_order_seed, file_identity, schedule_attempts, sha256_bytes, sha256_text, tree_digest
from chatgnt.records import ErrorInfo, GenerationResult, canonical_line, read_strict_json


def prompt_bytes():
    return canonical_line({"prompt_id": "p1", "prompt": "hello", "metadata": {}})


def manifest(frozen: bytes):
    project = load_project_configuration()
    base = project.model.values["base_model"]
    model_files, _ = read_strict_json(CONFIG_ROOT/"model-files.json")
    attempt = schedule_attempts(1, ["p1"], ["A"])[0].to_dict()
    implementation_files = [file_identity(path, PROJECT_ROOT) for path in sorted((PROJECT_ROOT/"chatgnt").glob("*.py")) if path.is_file()]
    digest = tree_digest(implementation_files)
    warmup_profile = replace(project.primary_profile,profile_id="warmup-sampled-v1",max_new_tokens=1).__dict__.copy()
    warmup_profile["eos_token_ids"] = list(warmup_profile["eos_token_ids"])
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
        "model": {"model_id": base["id"], "revision": base["revision"],
            "snapshot_path": f"artifacts/models/{base['id'].replace('/', '--')}/{base['revision']}",
            "architecture": base["architecture"], "model_type": "qwen2", "parameter_count": base["parameter_count"],
            "dtype": base["weight_dtype"], "max_context_tokens": base["max_context_tokens"],
            "weights_sha256": base["weights_sha256"], "behaviour_files": model_files["files"], "effective_generation_config": {}},
        "tokenizer": {"class": project.model.values["tokenizer"]["class"], "length": 151665,
            "chat_template_sha256": project.model.values["tokenizer"]["chat_template_sha256"],
            "eos_token_id": 151645, "generation_eos_token_ids": [151645,151643], "pad_token_id": 151643,
            "all_special_ids": [151643,151645]},
        "adapter": None,
        "configuration": {key: getattr(project,key).manifest_value() for key in ("model","generation","inference")},
        "environment": {"python":"3.12","platform":"x","torch":"x","transformers":"x","peft":"x",
            "tokenizers":"x","safetensors":"x","accelerate":"x","torch_cuda_build":"13.0",
            "cuda_driver":None,"cudnn":1,"device":"cuda:0","device_name":"fake",
            "device_total_memory_bytes":1,"bf16_supported":True,"attention_implementation":"sdpa",
            "collection_errors":[]},
        "timing": {"metric":"synchronized-model-generate","clock":"time.perf_counter_ns","cuda_synchronize":True,
            "include_prompt_prefill":True,"include_output_generation":True,"include_tokenization":False,
            "include_model_loading":False,"batch_size":1,"reusable_conversation_cache":False},
        "warmup": {"per_loaded_runtime":1,"profile":warmup_profile,"timed":False,"base_runtime_performed":True,
            "adapted_runtime_performed":False},
    }


def success_record():
    seed = schedule_attempts(1, ["p1"], ["A"])[0].generation_seed
    return {"schema_version":1,"run_id":"run-1","attempt_index":0,"prompt_id":"p1","system_id":"A",
        "repeat_index":0,"generation_seed":seed,"attempt_status":"success","adapter_enabled":False,
        "prompt_asset_id":"minimal","prompt_asset_sha256":"4"*64,
        "messages":[{"role":"system","content":""},{"role":"user","content":"hello"}],
        "rendered_prompt":"rendered","input_token_ids":[1,2],"input_token_count":2,
        "generated_token_ids":[7,151645],"generated_token_count":2,"visible_output_token_count":1,
        "raw_output":"value","raw_output_sha256":sha256_text("value"),"termination_reason":"eos_token",
        "terminal_token_id":151645,"reached_max_new_tokens":False,"generation_duration_ns":5,"error":None}


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

    def test_manifest_accepts_identity_captured_before_operational_files_exist(self):
        class Qwen2Tokenizer:
            eos_token_id=151645; all_special_ids=[151643,151645]; chat_template="template"
            def __len__(self): return 151665
        environment={"python":"3.12","platform":"x","torch":"x","transformers":"x","peft":"x",
            "tokenizers":"x","safetensors":"x","accelerate":"x","torch_cuda_build":"13.0",
            "cuda_driver":"580.126.20","cudnn":1,"device":"cuda:0","device_name":"fake",
            "device_total_memory_bytes":1,"bf16_supported":True,"attention_implementation":"sdpa",
            "collection_errors":[]}
        captured={"package_version":"0.1.0","behaviour_files":[],"behaviour_digest":"0"*64,
            "pyproject_sha256":"1"*64,"uv_lock_sha256":"2"*64,"git_commit":"3"*40,"git_dirty":False}
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); source=root/"minimal.json"; source.write_text("{}")
            asset=PromptAsset(source,"4"*64,1,"minimal","1",0,"")
            engine=SimpleNamespace(tokenizer=Qwen2Tokenizer(),device=SimpleNamespace(),runtime_evidence={
                "parameter_count":1543714304,"attention_implementation":"sdpa",
                "effective_generation_config":{},"adapter":None})
            with patch("chatgnt.harness._environment",return_value=environment), \
                 patch("chatgnt.harness._implementation_identity",side_effect=AssertionError("recaptured")):
                value=_make_manifest("run-1",root/"prompts.jsonl",b"source",[Prompt("p1","hello",{})],
                    prompt_bytes(),root/"systems.json",b"systems",[SystemDefinition("A",False,asset)],
                    schedule_attempts(1,["p1"],["A"]),load_project_configuration(),[],root/"snapshot",
                    {"base":engine},None,None,captured)
            self.assertEqual(value["implementation"],captured)


class EnvironmentTests(unittest.TestCase):
    def test_cuda_driver_is_collected_from_nvidia_smi(self):
        completed=SimpleNamespace(stdout="580.126.20\n")
        device=SimpleNamespace(index=0)
        properties=SimpleNamespace(total_memory=24_000_000_000)
        with patch("chatgnt.harness.subprocess.run",return_value=completed) as run, \
             patch("chatgnt.harness.platform.python_version",return_value="3.12"), \
             patch("chatgnt.harness.platform.platform",return_value="Linux"), \
             patch("chatgnt.harness._version",return_value="1"), \
             patch("chatgnt.harness.torch.cuda.get_device_name",return_value="NVIDIA L4"), \
             patch("chatgnt.harness.torch.cuda.get_device_properties",return_value=properties), \
             patch("chatgnt.harness.torch.cuda.is_bf16_supported",return_value=True), \
             patch("chatgnt.harness.torch.backends.cudnn.version",return_value=92000):
            value=_environment(device,"sdpa")
        self.assertEqual(value["cuda_driver"],"580.126.20")
        self.assertEqual(value["collection_errors"],[])
        self.assertEqual(run.call_args.args[0][1],"--id=0")


class RunnerTests(unittest.TestCase):
    class Qwen2Tokenizer:
        _tokenizer_config, _ = read_strict_json(PROJECT_ROOT/"artifacts/models/Qwen--Qwen2.5-1.5B-Instruct/989aa7980e4cf806f80c7fef2b1adb7bc71aa306/tokenizer_config.json")
        eos_token_id=151645; all_special_ids=[151643,151645]; chat_template=_tokenizer_config["chat_template"]
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
            model_files,_=read_strict_json(CONFIG_ROOT/"model-files.json")
            with patch("chatgnt.harness._verify_device",return_value=torch.device("cuda:0")), \
                 patch("chatgnt.harness.verify_model_files",return_value=model_files["files"]), \
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
                 patch("chatgnt.harness.verify_model_files",return_value=model_files["files"]), \
                 patch("chatgnt.harness.load_engine",return_value=fatal), \
                 patch("chatgnt.harness._environment",return_value=self.environment()):
                with self.assertRaises(RuntimeAbort):
                    execute_run(root/"prompts.jsonl",root/"systems.json",1,"cuda:0",
                        run_id="partial",runs_root=runs)
            partial=inspect_run(runs/"partial")
            self.assertFalse(partial["complete"]); self.assertEqual(partial["response_line_count"],1)


class InspectorTests(unittest.TestCase):
    def write_manifest(self, run: Path, value):
        (run/"manifest.json").write_bytes(canonical_line(value))

    def write_record(self, run: Path, value):
        (run/"responses.jsonl").write_bytes(canonical_line(value))

    def test_complete_run(self):
        with tempfile.TemporaryDirectory() as td:
            run=Path(td)/"run"; create_run(run,[canonical_line(success_record())])
            report=inspect_run(run)
            self.assertTrue(report["complete"]); self.assertEqual(report["valid_response_count"],1)

    def test_committed_historical_run_survives_later_package_files(self):
        run = PROJECT_ROOT / "experiments" / "runs" / "development-ab-v1-20260715"
        report = inspect_run(run)
        self.assertTrue(report["complete"], report["integrity_errors"])
        self.assertEqual(report["scheduled_count"], 40)
        self.assertEqual(report["valid_response_count"], 40)

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

    def test_collection_error_schema_types_and_order_are_enforced(self):
        mutations = [
            [{"field":"cuda_driver","type":"Error","extra":"x"}],
            [{"field":"cuda_driver","type":"Error","message":1}],
            [{"field":"z","type":"Error","message":"z"},{"field":"a","type":"Error","message":"a"}],
        ]
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            for index, errors in enumerate(mutations):
                with self.subTest(index=index):
                    run=base/f"run-{index}"; create_run(run,[canonical_line(success_record())])
                    value=manifest(prompt_bytes()); value["environment"]["collection_errors"]=errors
                    self.write_manifest(run,value)
                    report=inspect_run(run)
                    self.assertFalse(report["complete"]); self.assertTrue(report["integrity_errors"])

    def test_pinned_model_tokenizer_and_configuration_identity_are_enforced(self):
        mutations = [
            lambda value: value["model"].__setitem__("model_id","wrong/model"),
            lambda value: value["tokenizer"].__setitem__("eos_token_id",1),
            lambda value: value["configuration"]["generation"]["values"]["primary"].__setitem__("temperature",0.1),
            lambda value: value["configuration"]["model"].__setitem__("source_sha256","0"*64),
        ]
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            for index, mutate in enumerate(mutations):
                with self.subTest(index=index):
                    run=base/f"run-{index}"; create_run(run,[canonical_line(success_record())])
                    value=manifest(prompt_bytes()); mutate(value); self.write_manifest(run,value)
                    self.assertFalse(inspect_run(run)["complete"])

    def test_diagnostic_bypass_requires_fixed_adapter_identity(self):
        with tempfile.TemporaryDirectory() as td:
            run=Path(td)/"diagnostic"; create_run(run,[])
            value=manifest(prompt_bytes()); minimal=copy.deepcopy(value["system_set"]["systems"][0])
            minimal["system_id"]="C"; minimal["adapter_enabled"]=True
            value["system_set"]["systems"].append(minimal)
            schedule=schedule_attempts(1,["p1"],["A","C"])
            value["schedule"]["scheduled_attempt_count"]=len(schedule); value["schedule"]["attempts"]=[item.to_dict() for item in schedule]
            files=[{"path":"adapter_config.json","size_bytes":1,"sha256":"a"*64}]
            value["adapter"]={"path":{"kind":"project-relative","value":"artifacts/diagnostics/lora-lifecycle-adapter"},
                "adapter_id":"wrong-diagnostic-id","adapter_version":"unversioned-diagnostic",
                "adapter_digest":tree_digest(files),"behaviour_files":files,"provenance":None,
                "provenance_sha256":None,"peft_config":{},"active_adapters":["chatgnt"],
                "trainable_parameter_count":0,"parameter_dtypes":["torch.float32"],"merged":False}
            value["diagnostic"]=_diagnostic_declaration(); value["warmup"]["adapted_runtime_performed"]=True
            self.write_manifest(run,value)
            report=inspect_run(run)
            self.assertFalse(report["complete"]); self.assertTrue(report["integrity_errors"])

    def test_attempt_status_dependent_shapes_and_types_are_enforced(self):
        mutations = []
        def extra_message(record): record["messages"][0]["extra"]="x"
        mutations.append(extra_message)
        mutations.append(lambda record: record.__setitem__("rendered_prompt",7))
        mutations.append(lambda record: record.__setitem__("error",{"type":"Error","message":"bad"}))
        mutations.append(lambda record: record.__setitem__("schema_version",True))
        def invalid_failed_input(record):
            record.update({"attempt_status":"generation_error","generated_token_ids":[],"generated_token_count":0,
                "visible_output_token_count":0,"raw_output":None,"raw_output_sha256":None,
                "termination_reason":"error","terminal_token_id":None,"reached_max_new_tokens":False,
                "generation_duration_ns":None,"error":{"type":"ValueError","message":"bad"},"rendered_prompt":None})
        mutations.append(invalid_failed_input)
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            for index, mutate in enumerate(mutations):
                with self.subTest(index=index):
                    run=base/f"run-{index}"; create_run(run,[canonical_line(success_record())])
                    record=success_record(); mutate(record); self.write_record(run,record)
                    report=inspect_run(run)
                    self.assertFalse(report["complete"]); self.assertTrue(report["integrity_errors"])

    def test_missing_directory_exact_report_shape(self):
        with tempfile.TemporaryDirectory() as td:
            report=inspect_run(Path(td)/"absent")
            self.assertEqual(set(report), {"schema_version","run_id","scheduled_count","response_line_count",
                "valid_response_count","unique_recorded_attempt_count","missing_attempt_indices",
                "duplicate_attempt_indices","unexpected_attempt_indices","malformed_line_numbers",
                "integrity_errors","complete"})
            self.assertIsNone(report["run_id"])


if __name__ == "__main__": unittest.main()

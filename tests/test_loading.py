from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch

from chatgnt.configuration import load_project_configuration
from chatgnt.identity import sha256_text
from chatgnt.inference import RuntimeVerificationError, load_engine


class FakeParameter:
    def __init__(self, count=1543714304, device="cpu", name="base"):
        self._count=count; self.device=torch.device(device); self.dtype=torch.bfloat16; self.requires_grad=False; self.name=name
    def numel(self): return self._count
    def is_floating_point(self): return True


class FakeGenerationConfig:
    def to_dict(self): return {"do_sample": True}


class Qwen2ForCausalLM:
    def __init__(self, device="cpu"):
        self.parameter=FakeParameter(device=device)
        self.config=SimpleNamespace(model_type="qwen2",_attn_implementation="sdpa",max_position_embeddings=32768)
        self.generation_config=FakeGenerationConfig(); self.hf_device_map=None
    def parameters(self): return iter([self.parameter])
    def named_parameters(self): return iter([("weight",self.parameter)])
    def named_buffers(self): return iter([])
    def to(self,device): self.parameter.device=torch.device(device); return self
    def eval(self): return self


def tokenizer_class():
    def from_pretrained(path,**kwargs): return Qwen2Tokenizer()
    return SimpleNamespace(from_pretrained=unittest.mock.Mock(side_effect=from_pretrained))


class Qwen2Tokenizer:
    eos_token_id=151645; all_special_ids=[151643,151645]
    def __len__(self): return 151665
    @property
    def chat_template(self):
        # Loader checks the frozen digest, so return a value and patch the digest function in that module.
        return "template"


class FakePeftRuntime:
    def __init__(self, base):
        self.base=base; self.config=base.config; self.generation_config=base.generation_config
        self.active_adapters=["chatgnt"]; self.hf_device_map=None
        self.lora=FakeParameter(16,"cpu","lora"); self.lora.dtype=torch.float32
    def parameters(self): return iter([self.base.parameter,self.lora])
    def named_parameters(self): return iter([("base.weight",self.base.parameter),("lora_A.chatgnt.weight",self.lora)])
    def named_buffers(self): return iter([])
    def modules(self): return iter([])
    def eval(self): return self


class LoadingTests(unittest.TestCase):
    def test_formal_base_loading_keywords(self):
        project=load_project_configuration(); auto_model=SimpleNamespace(from_pretrained=unittest.mock.Mock(return_value=Qwen2ForCausalLM("cuda:0")))
        auto_tokenizer=tokenizer_class()
        fake_transformers=SimpleNamespace(AutoModelForCausalLM=auto_model,AutoTokenizer=auto_tokenizer)
        with patch.dict("sys.modules",{"transformers":fake_transformers}), patch("chatgnt.inference.sha256_text",return_value=project.model.values["tokenizer"]["chat_template_sha256"]):
            engine=load_engine(Path("snapshot"),"cuda:0","base",project,formal_cuda=True)
        kwargs=auto_model.from_pretrained.call_args.kwargs
        self.assertEqual(kwargs,{"local_files_only":True,"dtype":torch.bfloat16,"low_cpu_mem_usage":True,
            "attn_implementation":"sdpa","device_map":{"":torch.device("cuda:0")}})
        self.assertEqual(engine.runtime_mode,"base")

    def test_placement_mismatch_rejected(self):
        project=load_project_configuration(); auto_model=SimpleNamespace(from_pretrained=unittest.mock.Mock(return_value=Qwen2ForCausalLM("cpu")))
        fake_transformers=SimpleNamespace(AutoModelForCausalLM=auto_model,AutoTokenizer=tokenizer_class())
        with patch.dict("sys.modules",{"transformers":fake_transformers}), patch("chatgnt.inference.sha256_text",return_value=project.model.values["tokenizer"]["chat_template_sha256"]):
            with self.assertRaises(RuntimeVerificationError): load_engine(Path("snapshot"),"cuda:0","base",project,formal_cuda=True)

    def test_adapter_loading_keywords_and_unmerged_runtime(self):
        import peft
        project=load_project_configuration(); base=Qwen2ForCausalLM("cpu")
        auto_model=SimpleNamespace(from_pretrained=unittest.mock.Mock(return_value=base))
        fake_transformers=SimpleNamespace(AutoModelForCausalLM=auto_model,AutoTokenizer=tokenizer_class())
        adapter_path=Path("artifacts/diagnostics/lora-lifecycle-adapter")
        def load_adapter(model,path,**kwargs): return FakePeftRuntime(model)
        with patch.dict("sys.modules",{"transformers":fake_transformers}), \
             patch("chatgnt.inference.sha256_text",return_value=project.model.values["tokenizer"]["chat_template_sha256"]), \
             patch.object(peft.PeftModel,"from_pretrained",side_effect=load_adapter) as adapted:
            engine=load_engine(Path("snapshot"),"cpu","adapted",project,adapter_path,
                allow_unprovenanced_diagnostic_adapter=True,formal_cuda=False)
        self.assertEqual(adapted.call_args.kwargs,{"adapter_name":"chatgnt","is_trainable":False,
            "autocast_adapter_dtype":True,"ephemeral_gpu_offload":False,"low_cpu_mem_usage":False})
        evidence=engine.runtime_evidence["adapter"]
        self.assertEqual(evidence["active_adapters"],["chatgnt"]); self.assertEqual(evidence["trainable_parameter_count"],0)
        self.assertFalse(evidence["merged"]); self.assertEqual(evidence["parameter_dtypes"],["torch.float32"])


if __name__ == "__main__": unittest.main()

from contextlib import contextmanager
from dataclasses import replace
import unittest

import torch

from chatgnt.inference import InferenceEngine, installed_rng_state
from chatgnt.records import GenerationProfile, GenerationRequest, TimingPolicy


class FakeTokenizer:
    all_special_ids = [99]
    def __init__(self, ids=(1, 2), decoded="  untouched  "):
        self.ids = ids; self.decoded = decoded; self.template_call = None; self.decode_call = None
    def apply_chat_template(self, messages, **kwargs):
        self.template_call = (messages, kwargs); return "rendered"
    def __call__(self, rendered, **kwargs):
        self.tokenize_call = (rendered, kwargs)
        return {"input_ids": torch.tensor([self.ids]), "attention_mask": torch.ones((1, len(self.ids)), dtype=torch.long)}
    def decode(self, ids, **kwargs):
        self.decode_call = (ids, kwargs); return self.decoded


class FakeModel:
    def __init__(self, suffix=(7, 99), error=None, events=None):
        self.suffix = suffix; self.error = error; self.events = events if events is not None else []; self.kwargs = None
    def eval(self): self.events.append("eval"); return self
    def generate(self, **kwargs):
        self.events.append("generate"); self.kwargs = kwargs
        if self.error: raise self.error
        return torch.cat([kwargs["input_ids"].cpu(), torch.tensor([self.suffix])], dim=1)


def profile(maximum=2):
    return GenerationProfile("test-profile", True, .7, .8, 20, 1.1, maximum, 0, (99, 98), 98, 1, 1, True, "dynamic", False, False, False)


def request(seed=42, adapter=False):
    return GenerationRequest("p", " user ", "C" if adapter else "A", "asset", "0" * 64, " system ", adapter, 0, seed)


class EngineTests(unittest.TestCase):
    def test_exact_boundary_output_and_kwargs(self):
        tokenizer = FakeTokenizer(); model = FakeModel()
        engine = InferenceEngine(model, tokenizer, "cpu", "base", 4)
        result = engine.generate(request(), profile(), TimingPolicy("disabled", False, False, False))
        self.assertEqual(result.attempt_status, "success")
        self.assertEqual(list(result.messages), [{"role":"system","content":" system "},{"role":"user","content":" user "}])
        self.assertEqual(tokenizer.template_call[1], {"tokenize": False, "add_generation_prompt": True})
        self.assertEqual(tokenizer.tokenize_call[1], {"add_special_tokens": False, "truncation": False, "return_tensors": "pt"})
        self.assertEqual(result.generated_token_ids, (7, 99)); self.assertEqual(result.visible_output_token_count, 1)
        self.assertEqual(result.raw_output, "  untouched  ")
        self.assertEqual(tokenizer.decode_call, ([7, 99], {"skip_special_tokens": True, "clean_up_tokenization_spaces": False}))
        self.assertNotIn("generator", model.kwargs); self.assertNotIn("stop_strings", model.kwargs)
        self.assertEqual(set(model.kwargs) - {"input_ids", "attention_mask"}, set(profile().generation_kwargs()))

    def test_context_gate_both_sides(self):
        engine = InferenceEngine(FakeModel(), FakeTokenizer(), "cpu", "base", 4)
        accepted = engine.generate(request(), profile(2), TimingPolicy("off", False, False, False))
        self.assertEqual(accepted.attempt_status, "success")
        rejected = InferenceEngine(FakeModel(), FakeTokenizer(ids=(1,2,3)), "cpu", "base", 4).generate(request(), profile(2), TimingPolicy("off", False, False, False))
        self.assertEqual(rejected.attempt_status, "input_context_exceeded")
        self.assertEqual(rejected.input_token_ids, (1,2,3)); self.assertIsNone(rejected.generation_duration_ns)

    def test_timing_event_order(self):
        events=[]; values=iter((100, 145))
        model=FakeModel(events=events)
        def sync(): events.append("sync")
        def clock(): events.append("clock"); return next(values)
        @contextmanager
        def rng(_device, _seed): yield
        engine=InferenceEngine(model, FakeTokenizer(), "cpu", "base", 4, clock, sync, rng_installer=rng)
        result=engine.generate(request(), profile(), TimingPolicy("metric", True, True, False))
        self.assertEqual(events, ["eval", "sync", "clock", "generate", "sync", "clock"])
        self.assertEqual(result.generation_duration_ns, 45)

    def test_eos_wins_at_maximum_and_maximum_without_eos(self):
        engine=InferenceEngine(FakeModel((7,99)), FakeTokenizer(), "cpu", "base", 4)
        eos=engine.generate(request(), profile(), TimingPolicy("off",False,False,False))
        self.assertEqual(eos.termination_reason,"eos_token"); self.assertTrue(eos.reached_max_new_tokens)
        maximum=InferenceEngine(FakeModel((7,8)), FakeTokenizer(), "cpu", "base", 4).generate(request(), profile(), TimingPolicy("off",False,False,False))
        self.assertEqual(maximum.termination_reason,"max_new_tokens"); self.assertIsNone(maximum.terminal_token_id)

    def test_unexpected_termination_and_prefix_failure_are_fatal(self):
        short=InferenceEngine(FakeModel((7,)), FakeTokenizer(), "cpu", "base", 4)
        result=short.generate(request(), profile(), TimingPolicy("off",False,False,False))
        self.assertEqual(result.error.type,"UnexpectedTerminationError"); self.assertTrue(short.last_failure_fatal)
        class Wrong(FakeModel):
            def generate(self, **kwargs): return torch.tensor([[9,2,7,99]])
        wrong=InferenceEngine(Wrong(), FakeTokenizer(), "cpu", "base", 4)
        result=wrong.generate(request(),profile(),TimingPolicy("off",False,False,False))
        self.assertEqual(result.error.type,"OutputInvariantError")

    def test_generation_error_classification(self):
        isolated=InferenceEngine(FakeModel(error=ValueError("isolated")),FakeTokenizer(),"cpu","base",4)
        result=isolated.generate(request(),profile(),TimingPolicy("off",False,False,False))
        self.assertFalse(isolated.last_failure_fatal); self.assertIsNone(result.generation_duration_ns)
        fatal=InferenceEngine(FakeModel(error=RuntimeError("device")),FakeTokenizer(),"cpu","base",4)
        fatal.generate(request(),profile(),TimingPolicy("off",False,False,False)); self.assertTrue(fatal.last_failure_fatal)

    def test_sync_error_is_fatal(self):
        def sync(): raise RuntimeError("sync")
        @contextmanager
        def rng(_device,_seed): yield
        engine=InferenceEngine(FakeModel(),FakeTokenizer(),"cpu","base",4,cuda_synchronizer=sync,rng_installer=rng)
        result=engine.generate(request(),profile(),TimingPolicy("metric",True,True,False))
        self.assertEqual(result.error.type,"RuntimeError"); self.assertTrue(engine.last_failure_fatal)

    def test_runtime_mode_refuses_substitution(self):
        engine=InferenceEngine(FakeModel(),FakeTokenizer(),"cpu","base",4)
        with self.assertRaises(ValueError): engine.generate(request(adapter=True),profile(),TimingPolicy("off",False,False,False))

    def test_rng_restored_and_independent_of_history(self):
        before=torch.random.get_rng_state().clone()
        with installed_rng_state(torch.device("cpu"),123): first=torch.randint(0,1000,(5,))
        self.assertTrue(torch.equal(torch.random.get_rng_state(),before))
        torch.manual_seed(999); prior=torch.random.get_rng_state().clone()
        with installed_rng_state(torch.device("cpu"),123): second=torch.randint(0,1000,(5,))
        self.assertTrue(torch.equal(first,second)); self.assertTrue(torch.equal(torch.random.get_rng_state(),prior))
        try:
            with installed_rng_state(torch.device("cpu"),123): raise ValueError("boom")
        except ValueError: pass
        self.assertTrue(torch.equal(torch.random.get_rng_state(),prior))

    def test_keyboard_interrupt_is_not_converted_to_a_record(self):
        engine=InferenceEngine(FakeModel(error=KeyboardInterrupt()),FakeTokenizer(),"cpu","base",4)
        with self.assertRaises(KeyboardInterrupt):
            engine.generate(request(),profile(),TimingPolicy("off",False,False,False))


if __name__ == "__main__": unittest.main()

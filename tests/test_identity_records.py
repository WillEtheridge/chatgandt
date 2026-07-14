import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from chatgnt.identity import execution_order_seed, generation_seed, schedule_attempts, sha256_text
from chatgnt.records import ContractError, canonical_json, strict_json_loads


class JsonContractTests(unittest.TestCase):
    def test_canonical_json(self):
        self.assertEqual(canonical_json({"z": 1, "é": "x"}), '{"z":1,"é":"x"}')

    def test_duplicate_key_rejected(self):
        with self.assertRaisesRegex(ContractError, "duplicate"):
            strict_json_loads('{"a":1,"a":2}')

    def test_nonfinite_rejected(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.assertRaises(ContractError):
                strict_json_loads('{"a":' + value + "}")

    def test_bool_is_not_integer_in_seed(self):
        with self.assertRaises(ContractError):
            generation_seed(True, "p", 0)


class IdentityTests(unittest.TestCase):
    def test_fixed_seed_vectors(self):
        self.assertEqual(generation_seed(0, "dev-001", 0), 11288511147500510643)
        self.assertEqual(generation_seed(20260714, "dev-001", 0), 5101397657945493966)
        self.assertEqual(generation_seed(20260714, "dev-001", 1), 17799120203909364911)
        self.assertEqual(execution_order_seed(0), 1107510439186287908)
        self.assertEqual(execution_order_seed(20260714), 17625029341685692511)

    def test_generation_seed_excludes_system(self):
        values = [generation_seed(7, "same", 0) for _system in "ABCD"]
        self.assertEqual(len(set(values)), 1)

    def test_schedule_conformance_and_coverage(self):
        schedule = schedule_attempts(20260714, ["p1", "p2"], ["D", "B", "A", "C"])
        self.assertEqual([(x.prompt_id, x.system_id) for x in schedule], [
            ("p1", "C"), ("p2", "B"), ("p1", "D"), ("p1", "A"),
            ("p1", "B"), ("p2", "C"), ("p2", "D"), ("p2", "A")])
        self.assertEqual([x.attempt_index for x in schedule], list(range(8)))
        self.assertEqual(len({(x.prompt_id, x.system_id, x.repeat_index) for x in schedule}), 8)


if __name__ == "__main__":
    unittest.main()

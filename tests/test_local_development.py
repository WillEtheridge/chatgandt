import unittest

from chatgnt.local_development import LOCAL_RUN_SEED, LOCAL_SEED_MODULUS, local_prompt_seed


class LocalPromptSeedTests(unittest.TestCase):
    def test_seed_is_stable_positive_and_prompt_specific(self):
        first = local_prompt_seed("dev-v1-advice-clean")
        self.assertEqual(first, local_prompt_seed("dev-v1-advice-clean", LOCAL_RUN_SEED))
        self.assertGreaterEqual(first, 0)
        self.assertLess(first, LOCAL_SEED_MODULUS)
        self.assertNotEqual(first, local_prompt_seed("dev-v1-explanation-clean"))


if __name__ == "__main__":
    unittest.main()

"""Tests for explicit, loss-aware interactive context recovery."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_generate_module():
    torch = types.ModuleType("torch")
    distributed = types.ModuleType("torch.distributed")
    torch.distributed = distributed
    torch.Tensor = object
    torch.bfloat16 = object()
    torch.inference_mode = lambda: (lambda function: function)
    torch.set_default_dtype = lambda _dtype: None

    transformers = types.ModuleType("transformers")
    transformers.AutoTokenizer = object
    safetensors = types.ModuleType("safetensors")
    safetensors_torch = types.ModuleType("safetensors.torch")
    safetensors_torch.load_model = lambda *_args, **_kwargs: None
    model = types.ModuleType("model")
    model.Transformer = object
    model.ModelArgs = object

    spec = importlib.util.spec_from_file_location(
        "generate_context_recovery_under_test",
        ROOT / "inference" / "generate.py",
    )
    module = importlib.util.module_from_spec(spec)
    stubs = {
        "torch": torch,
        "torch.distributed": distributed,
        "transformers": transformers,
        "safetensors": safetensors,
        "safetensors.torch": safetensors_torch,
        "model": model,
    }
    with patch.dict(sys.modules, stubs):
        spec.loader.exec_module(module)
    return module


class InteractiveContextRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_generate_module()

    def test_prompt_budget_reserves_requested_output_tokens(self):
        fits = self.module._prompt_fits_context
        self.assertTrue(fits(prompt_token_count=80, max_new_tokens=20, max_seq_len=100))
        self.assertTrue(fits(prompt_token_count=99, max_new_tokens=1, max_seq_len=100))
        self.assertFalse(fits(prompt_token_count=81, max_new_tokens=20, max_seq_len=100))
        self.assertFalse(fits(prompt_token_count=100, max_new_tokens=1, max_seq_len=100))

    def test_negative_budgets_are_rejected(self):
        fits = self.module._prompt_fits_context
        self.assertFalse(fits(prompt_token_count=1, max_new_tokens=-1, max_seq_len=100))
        self.assertFalse(fits(prompt_token_count=-1, max_new_tokens=1, max_seq_len=100))

    def test_drop_oldest_removes_only_a_complete_user_assistant_turn(self):
        messages = [
            {"role": "user", "content": "old question"},
            {"role": "assistant", "content": "old answer"},
            {"role": "user", "content": "new question"},
            {"role": "assistant", "content": "new answer"},
        ]
        self.assertTrue(self.module._drop_oldest_complete_turn(messages))
        self.assertEqual(
            messages,
            [
                {"role": "user", "content": "new question"},
                {"role": "assistant", "content": "new answer"},
            ],
        )

    def test_drop_oldest_does_not_remove_an_incomplete_turn(self):
        messages = [{"role": "user", "content": "pending question"}]
        before = list(messages)
        self.assertFalse(self.module._drop_oldest_complete_turn(messages))
        self.assertEqual(messages, before)

    def test_drop_oldest_does_not_remove_an_unexpected_message_pair(self):
        messages = [
            {"role": "assistant", "content": "unexpected first message"},
            {"role": "user", "content": "question"},
        ]
        before = list(messages)
        self.assertFalse(self.module._drop_oldest_complete_turn(messages))
        self.assertEqual(messages, before)


if __name__ == "__main__":
    unittest.main()

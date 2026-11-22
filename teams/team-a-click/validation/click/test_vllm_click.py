"""GPU-free regression checks for native vLLM input/score auditing."""

import unittest
from types import SimpleNamespace

from vllm_click import Audit, tokens_for


class Engine:
    def generate(self, prompts, **kwargs):
        outputs = []
        for prompt in prompts:
            ids = prompt["prompt_token_ids"]
            outputs.append(
                SimpleNamespace(
                    prompt_token_ids=ids,
                    prompt_logprobs=[None]
                    + [
                        {t: SimpleNamespace(logprob=-float(i))}
                        for i, t in enumerate(ids[1:], 1)
                    ],
                )
            )
        return outputs


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.engine = Engine()
        self.audit = Audit(self.engine)
        self.tokens = {"context": [11, 12], "continuations": [[21], [22, 23]]}
        self.audit.begin(self.tokens)

    def test_candidate_positions_exclude_prompt_and_include_last_token(self):
        self.engine.generate(
            [{"prompt_token_ids": [11, 12, 22, 23]}, {"prompt_token_ids": [11, 12, 21]}]
        )
        self.assertEqual(self.audit.finish(self.tokens, [-2, -5]), [[-2], [-2, -3]])

    def test_truncation_or_added_bos_is_rejected(self):
        for ids in ([12, 21], [0, 11, 12, 21]):
            with self.assertRaises(ValueError):
                self.engine.generate([{"prompt_token_ids": ids}])

    def test_missing_candidate_is_rejected(self):
        self.engine.generate([{"prompt_token_ids": [11, 12, 21]}])
        with self.assertRaises(ValueError):
            self.audit.finish(self.tokens, [-2, -5])

    def test_wrong_scored_boundary_is_rejected(self):
        self.engine.generate(
            [{"prompt_token_ids": [11, 12, 21]}, {"prompt_token_ids": [11, 12, 22, 23]}]
        )
        with self.assertRaises(ValueError):
            self.audit.finish(self.tokens, [-3, -6])

    def test_missing_actual_token_logprob_is_rejected(self):
        def missing(prompts, **kwargs):
            return [
                SimpleNamespace(
                    prompt_token_ids=[11, 12, 21],
                    prompt_logprobs=[None, {}, {999: SimpleNamespace(logprob=-2)}],
                )
            ]

        self.audit.original = missing
        with self.assertRaises(ValueError):
            self.engine.generate([{"prompt_token_ids": [11, 12, 21]}])

    def test_cross_boundary_token_merge_is_rejected(self):
        class Tokenizer:
            def encode(self, text, **kwargs):
                return {"ctx": [1], " A": [2], "ctx A": [3]}[text]

        with self.assertRaises(ValueError):
            tokens_for(Tokenizer(), {"query": "ctx", "choices": [" A"]})


if __name__ == "__main__":
    unittest.main()

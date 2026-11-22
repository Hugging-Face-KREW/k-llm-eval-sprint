"""Regression checks for read-only auditing of real Transformers forward shapes."""

import unittest
from types import SimpleNamespace

import torch
from transformers_click import ForwardAudit


class AuditTests(unittest.TestCase):
    def test_native_full_input_right_padding_and_final_target(self):
        audit = ForwardAudit(
            {"context": [1, 2], "continuations": [[3], [3, 1]]}, 0, False
        )
        ids = torch.tensor([[1, 2, 3, 0], [1, 2, 3, 1]])
        audit.before(None, (ids,), {})
        audit.after(
            None,
            (ids,),
            {},
            SimpleNamespace(logits=torch.zeros(2, 4, 4, dtype=torch.bfloat16)),
        )
        result = audit.finish([-1.3828125, -2.765625])
        self.assertEqual([len(x["tokens"]) for x in result], [1, 2])

    def test_harness_shared_prefix_still_scores_distinct_targets(self):
        audit = ForwardAudit({"context": [1, 2], "continuations": [[3], [1]]}, 0, True)
        for _ in range(2):
            ids = torch.tensor([[1, 2]])
            audit.before(None, (ids,), {})
            audit.after(
                None,
                (ids,),
                {},
                SimpleNamespace(logits=torch.zeros(1, 2, 4, dtype=torch.bfloat16)),
            )
        self.assertEqual(len(audit.finish([-1.3828125, -1.3828125])), 2)

    def test_added_bos_truncation_and_wrong_padding_are_rejected(self):
        for ids in ([[9, 1, 2, 3]], [[2, 3]], [[1, 2, 3, 9]]):
            audit = ForwardAudit({"context": [1, 2], "continuations": [[3]]}, 0, False)
            with self.assertRaises(ValueError):
                audit.before(None, (torch.tensor(ids),), {})

    def test_wrong_native_score_and_missing_forward_are_rejected(self):
        audit = ForwardAudit({"context": [1, 2], "continuations": [[3]]}, 0, False)
        with self.assertRaises(ValueError):
            audit.finish([-1.3828125])
        ids = torch.tensor([[1, 2, 3]])
        audit.before(None, (ids,), {})
        audit.after(
            None,
            (ids,),
            {},
            SimpleNamespace(logits=torch.zeros(1, 3, 4, dtype=torch.bfloat16)),
        )
        with self.assertRaises(ValueError):
            audit.finish([-2.765625])


if __name__ == "__main__":
    unittest.main()

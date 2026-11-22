"""CPU checks for the FP32 runner's dtype, placement and condition branches."""

import unittest
from types import SimpleNamespace
from unittest import mock

import torch

import transformers_click as tc
import transformers_fp32 as fp

UUIDS = [g["uuid"] for g in fp.GPUS]


class FP32Tests(unittest.TestCase):
    def test_placement_kwargs(self):
        self.assertEqual(fp.load_kwargs(fp.PLACEMENT["kanana2-3b"]), ({}, "cuda:0"))
        kwargs, device = fp.load_kwargs(fp.PLACEMENT["qwen38-27b"])
        self.assertIsNone(device)
        self.assertEqual(kwargs["device_map"], "sequential")
        self.assertEqual(kwargs["max_memory"], {0: "50GiB", 1: "70GiB"})

    def test_device_order_must_match_protocol(self):
        fp.check_devices(fp.GPUS, UUIDS)
        for wrong in (UUIDS[::-1], UUIDS[:1], UUIDS + ["GPU-other"]):
            with self.assertRaises(ValueError):
                fp.check_devices(fp.GPUS, wrong)

    def test_run_swaps_only_backend_and_conditions(self):
        seen = {}

        def fake_run(args):
            seen.update(backend=tc.Backend, conditions=tc.CONDITIONS)

        with (
            mock.patch.object(tc, "run", fake_run),
            mock.patch.object(tc, "Backend", tc.Backend),
            mock.patch.object(tc, "CONDITIONS", tc.CONDITIONS),
        ):
            fp.run(None)
        self.assertIs(seen["backend"], fp.Backend)
        # tc.run picks CONDITIONS[:1] for lighteval and CONDITIONS[1:] for harness.
        self.assertEqual(seen["conditions"][:1], ("lighteval_full",))
        self.assertEqual(
            seen["conditions"][1:],
            ("aligned_harness_full", "base_letter", "pr4420_letter"),
        )
        self.assertEqual(len(tc.CONDITIONS), 6)  # restored

    def test_bf16_logits_and_offloaded_weights_are_rejected(self):
        good = {
            "forward_audit": {
                "passed": True,
                "logits_dtype": fp.FP32,
                "sum_dtype": fp.FP32,
            }
        }
        fp.require_fp32(good)
        bad = {
            "forward_audit": {**good["forward_audit"], "logits_dtype": "torch.bfloat16"}
        }
        with self.assertRaises(ValueError):
            fp.require_fp32(bad)
        model = torch.nn.Linear(2, 2)
        with self.assertRaises(ValueError):
            fp.placement_record(model, "cuda:0")  # parameters are really on CPU

    def test_busy_gpu_detection(self):
        ours, other = UUIDS[0], "GPU-7ab58b2a"
        memory = f"{ours}, 15\n{UUIDS[1]}, 15\n"
        self.assertEqual(fp.occupied(f"{other}, 1, 900\n", memory, set(UUIDS)), [])
        self.assertTrue(fp.occupied(f"{ours}, 1, 900\n", memory, set(UUIDS)))
        self.assertTrue(fp.occupied("", f"{ours}, 4000\n", set(UUIDS)))

    def test_forward_audit_records_fp32_logits(self):
        audit = tc.ForwardAudit({"context": [1, 2], "continuations": [[3]]}, 0, False)
        ids = torch.tensor([[1, 2, 3]])
        audit.before(None, (ids,), {})
        audit.after(None, (ids,), {}, SimpleNamespace(logits=torch.zeros(1, 3, 4)))
        value = audit.finish([-1.3862943649291992])[0]
        fp.require_fp32(
            {
                "forward_audit": {
                    "passed": True,
                    "logits_dtype": value["logits_dtype"],
                    "sum_dtype": value["sum_dtype"],
                }
            }
        )


if __name__ == "__main__":
    unittest.main()

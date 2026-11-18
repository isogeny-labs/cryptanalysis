#!/usr/bin/env python3
"""CT190 source-only falsification; NO native executable and no paid benchmark."""
import copy
import json
import unittest

import ct190_norm_reuse_source_audit as audit


class CT190NormReuseSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = audit.load_sources()

    def mutate(self, name, old, new):
        files = dict(self.original)
        raw = files[name]
        old, new = old.encode(), new.encode()
        self.assertEqual(raw.count(old), 1, (name, old))
        files[name] = raw.replace(old, new, 1)
        return files

    def test_frozen_original_optimized_counter_bridge(self):
        result = audit.audit(self.original)
        self.assertTrue(result["verified_source_contract"])
        self.assertEqual((result["counter_fields_original"],
                          result["counter_fields_norm_reuse"]), (20, 21))
        self.assertEqual(result["observed_frozen_packets"], 48)
        self.assertEqual(result["old_git_blob"], audit.PINNED_BLOBS["old"])
        self.assertEqual(result["optimized_git_blob"], audit.PINNED_BLOBS["reuse"])
        self.assertEqual(result["frozen_fixture_git_blob"],
                         audit.PINNED_BLOBS["fixture"])
        for key in ("native_executable_source_attested",
                    "native_compilation_or_timing_performed",
                    "measured_n2_actual_or_d_padd",
                    "complete_single_target_ecdlp_advantage_established"):
            self.assertIs(result[key], False)

    def test_real_norm_math_path_must_not_be_replaced_by_proxy(self):
        src = self.mutate(
            "reuse",
            "descend_point(curve::pmul(&target.f, &target.curve, &point, 2))",
            "curve::padd(&target.f, &target.curve, &point, &point)")
        with self.assertRaisesRegex(ValueError, "pmul"):
            audit.audit(src, enforce_pins=False)
        with self.assertRaisesRegex(ValueError, "Git blob changed"):
            audit.audit(src)

    def test_direct_and_retained_must_still_use_norm_reuse(self):
        src = self.mutate(
            "reuse", "let norm = self.norm_point(to, point);",
            "let norm = self.norm_point_old(to, point);")
        with self.assertRaisesRegex(ValueError, "direct and retained"):
            audit.audit(src, enforce_pins=False)

    def test_nonreuse_cargo_target_is_rejected(self):
        src = self.mutate(
            "cargo", 'path = "../../fixed-jacobian-chain-evaluator-02"',
            'path = "../../fixed-jacobian-chain-evaluator-01"')
        with self.assertRaisesRegex(ValueError, "Cargo dependency"):
            audit.audit(src, enforce_pins=False)

    def test_cold_cli_swap_rejected(self):
        src = self.mutate(
            "rust",
            'let cold_requested = args.first().is_some_and(|a| a == "--cold-route");',
            'let cold_requested = args.first().is_some_and(|a| a == "--cold-other");')
        with self.assertRaisesRegex(ValueError, "cold-execute"):
            audit.audit(src, enforce_pins=False)

    def test_collector_reader_contract_drift_rejected(self):
        src = self.mutate("reader", "len(counts) == 21", "len(counts) == 22")
        with self.assertRaisesRegex(ValueError, "21 optimized"):
            audit.audit(src, enforce_pins=False)

    def test_physical_arm_cannot_become_sham(self):
        src = self.mutate(
            "crossover",
            "native.run_sample(binary, packet, physical_arm, rows[packet], allowance)",
            'native.run_sample(binary, packet, "direct_composite", rows[packet], allowance)')
        with self.assertRaisesRegex(ValueError, "real physical route"):
            audit.audit(src, enforce_pins=False)

    def test_frozen_counter_mismatch_rejected_even_if_hash_gate_bypassed(self):
        src = dict(self.original)
        payload = json.loads(src["fixture"])
        payload["all48"][0]["direct_composite"]["transported_norm_doubling"] = 0
        src["fixture"] = json.dumps(payload).encode()
        with self.assertRaisesRegex(ValueError, "wrong actual norm/map counts"):
            audit.audit(src, enforce_pins=False)
        with self.assertRaisesRegex(ValueError, "fixture Git blob changed"):
            audit.audit(src)

    def test_different_fixture_counter_schema_refused(self):
        src = dict(self.original)
        payload = json.loads(src["fixture"])
        del payload["all48"][0]["strongest_retained_lift_chain"]["transported_norm_doubling"]
        src["fixture"] = json.dumps(payload).encode()
        with self.assertRaisesRegex(ValueError, "counter names differ"):
            audit.audit(src, enforce_pins=False)

    def test_missing_frozen_evidence_refused(self):
        src = dict(self.original)
        del src["old"]
        with self.assertRaisesRegex(ValueError, "missing/unexpected"):
            audit.audit(src)


if __name__ == "__main__":
    unittest.main()

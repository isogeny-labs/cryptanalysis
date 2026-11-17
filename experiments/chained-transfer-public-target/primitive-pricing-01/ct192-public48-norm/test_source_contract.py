#!/usr/bin/env python3
"""CT192 source and real public fixture sabotage controls; no Rust executed."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch
import source_contract as ct

class CT192(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = ct.ORIGINAL.read_bytes()
        cls.fixture = ct.FROZEN.read_bytes()
        cls.driver = (ct.HERE / "src/main.rs").read_bytes()
        cls.cargo = (ct.HERE / "Cargo.toml").read_bytes()

    def test_authentic_48_and_96_selected_operands(self):
        result = ct.audit()
        self.assertEqual(result["packets"], 48)
        self.assertEqual(result["exceptional"], 8)
        self.assertEqual(result["pre_norm_route_operands"], 96)
        self.assertFalse(result["native_executed"])
        self.assertTrue(result["source_audit_passed"])

    def test_CT125_unchanged_exact_git_blob(self):
        self.assertEqual(ct.blob(self.original), ct.ORIGINAL_BLOB)

    def test_original_48_unchanged_exact_git_blob(self):
        self.assertEqual(ct.blob(self.fixture), ct.FROZEN_BLOB)

    def test_reject_arithmetic_mutation(self):
        mutation = self.original.replace(
            b"descend_point(curve::pmul(&target.f, &target.curve, &point, 2))",
            b"descend_point(curve::padd(&target.f, &target.curve, &point, &point))")
        self.assertNotEqual(mutation, self.original)
        with self.assertRaises(ValueError):
            ct.derivative(mutation)

    def test_only_six_exact_source_anchors_modified(self):
        derivative = ct.derivative(self.original)
        self.assertIn(b"ct192_pre_norm_operand", derivative)
        self.assertIn(b"ct192_actual_norm", derivative)
        self.assertIn(ct.NORM_ANCHOR.encode(), derivative)
        self.assertIn(b"self.gamma(1, to, self.gamma(from, 1, lifted)?)?", derivative)
        self.assertIn(b"descend_point(curve::pmul(&target.f, &target.curve, &point, 2))", derivative)
        self.assertNotIn(b"scalar_OUTSIDE_runtime", ct.PROBE.encode())
        self.assertNotIn(b"generator()", ct.PROBE.encode())

    def test_reject_missing_and_duplicate_public_cohorts(self):
        raw = json.loads(self.fixture)
        for variant in ("missing", "duplicate"):
            x = json.loads(json.dumps(raw))
            if variant == "missing":
                x["all48"].pop()
            else:
                x["all48"][1] = x["all48"][0]
            data = json.dumps(x).encode()
            with patch.object(ct, "FROZEN_BLOB", ct.blob(data)):
                with self.assertRaises(ValueError):
                    ct.validate_fixture(data)

    def test_reject_changed_19_word_key_and_counter_schema(self):
        raw = json.loads(self.fixture)
        for mode in ("bad_key", "missing_counter", "boolean_counter"):
            x = json.loads(json.dumps(raw))
            if mode == "bad_key":
                x["all48"][0]["input"].pop()
            elif mode == "missing_counter":
                x["all48"][0]["direct_composite"].pop("transported_norm_doubling")
            else:
                x["all48"][0]["direct_composite"]["transported_norm_doubling"] = True
            data = json.dumps(x).encode()
            with patch.object(ct, "FROZEN_BLOB", ct.blob(data)):
                with self.assertRaises(ValueError):
                    ct.validate_fixture(data)

    def test_reject_driver_scalar_reconstruction(self):
        changed = self.driver + b"\n// curve::pmul(source.generator(), secret)\n"
        with self.assertRaises(ValueError):
            ct.source_audit(changed, self.cargo)

    def test_reject_missing_true_norm_method(self):
        mutated = self.driver.replace(b"ct192_actual_norm", b"ct192_fake_norm")
        self.assertNotEqual(mutated, self.driver)
        with self.assertRaises(ValueError):
            ct.source_audit(mutated, self.cargo)

    def test_reject_manifest_dependency_swap(self):
        altered = self.cargo.replace(b"ghs-original-engines =", b"fake-engine =")
        self.assertNotEqual(altered, self.cargo)
        with self.assertRaises(ValueError):
            ct.source_audit(self.driver, altered)

    def test_reject_previously_generated_uncontrolled_rust(self):
        with TemporaryDirectory() as tmp:
            f = Path(tmp) / "lib.rs"
            f.write_bytes(ct.derivative(self.original) + b"\n// post-audit mutation\n")
            with patch.object(ct, "GENERATED", f):
                with self.assertRaises(ValueError):
                    ct.audit()

if __name__ == "__main__":
    main()

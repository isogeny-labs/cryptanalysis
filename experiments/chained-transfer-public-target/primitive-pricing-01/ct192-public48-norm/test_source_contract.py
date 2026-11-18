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

    def test_CT193_full_target_class_binding_is_in_guarded_derivative(self):
        derived = ct.derivative(self.original)
        ct.validate_class_binding(derived)
        self.assertIn(
            b"if self.target_phi(to, operand)? != result.class {",
            derived,
        )
        self.assertIn(
            b"if result.norm != self.norm_point(to, operand) {",
            derived,
        )
        self.assertTrue(ct.audit()["source_audit_passed"])

    def test_CT193_reject_norm_only_or_misordered_class_validation(self):
        derived = ct.derivative(self.original)
        wrong = derived.replace(
            b"if self.target_phi(to, operand)? != result.class {",
            b"if self.norm_point(to, operand) != result.norm {",
        )
        self.assertNotEqual(derived, wrong)
        with self.assertRaises(ValueError):
            ct.validate_class_binding(wrong)
        swapped_order = derived.replace(
            b"        if self.target_phi(to, operand)? != result.class {\n"
            b"            return Err(\"CT193 pre-norm point differs from native target class\".into());\n"
            b"        }\n"
            b"        self.check_final(&result)?;",
            b"        self.check_final(&result)?;\n"
            b"        if self.target_phi(to, operand)? != result.class {\n"
            b"            return Err(\"CT193 pre-norm point differs from native target class\".into());\n"
            b"        }",
        )
        self.assertNotEqual(derived, swapped_order)
        with self.assertRaises(ValueError):
            ct.validate_class_binding(swapped_order)

    def test_CT193_doubling_not_injective_on_F5_elliptic_curve(self):
        # E/F_5: y^2 = x^3 - x, discriminant = 64 != 0 mod 5.
        # P=(2,1), Q=P+(0,0)=(2,4) are distinct yet 2P=2Q.
        prime = 5
        def add(p, q):
            if p is None:
                return q
            if q is None:
                return p
            x, y = p
            X, Y = q
            if x == X and (y + Y) % prime == 0:
                return None
            if p == q:
                slope = ((3*x*x - 1) * pow(2*y, -1, prime)) % prime
            else:
                slope = ((Y-y) * pow(X-x, -1, prime)) % prime
            outx = (slope*slope-x-X) % prime
            outy = (slope*(x-outx)-y) % prime
            return (outx, outy)
        P, T = (2, 1), (0, 0)
        Q = add(P, T)
        self.assertEqual(64 % prime, 4)
        for point in (P, T, Q):
            x, y = point
            self.assertEqual((y*y-x*x*x+x) % prime, 0)
        self.assertIsNone(add(T, T))
        self.assertNotEqual(P, Q)
        self.assertEqual(Q, (2, 4))
        self.assertEqual(add(P, P), (0, 0))
        self.assertEqual(add(P, P), add(Q, Q))

    def test_CT194_real_both_arm_per_iteration_input_opacity(self):
        ct.validate_opaque_timing(self.driver)
        ct.source_audit(self.driver, self.cargo)
        self.assertEqual(self.driver.count(b"let measured_operand = black_box(point);"), 2)

    def test_CT194_reject_missing_or_moved_input_barrier(self):
        removed = self.driver.replace(
            b"let measured_operand = black_box(point);",
            b"let measured_operand = point;",
        )
        self.assertNotEqual(removed, self.driver)
        with self.assertRaises(ValueError):
            ct.validate_opaque_timing(removed)
        old = b"                for _ in 0..64 {\n"
        new = b"                let measured_operand = black_box(point);\n                for _ in 0..64 {\n"
        moved = self.driver.replace(old, new).replace(
            b"                    let measured_operand = black_box(point);\n", b"",
        )
        self.assertNotEqual(moved, self.driver)
        with self.assertRaises(ValueError):
            ct.validate_opaque_timing(moved)

    def test_CT194_reject_asymmetric_opaque_input_or_output(self):
        mutations = (
            (
                b"ct192_actual_norm(to, measured_operand)",
                b"ct192_actual_norm(to, point)",
            ),
            (
                b"&measured_operand, &measured_operand)),",
                b"&point, &point)),",
            ),
            (
                b'"D_padd" => black_box(curve::padd(',
                b'"D_padd" => curve::padd(',
            ),
        )
        for old, new in mutations:
            with self.subTest(old=old):
                mutated = self.driver.replace(old, new)
                self.assertNotEqual(mutated, self.driver)
                with self.assertRaises(ValueError):
                    ct.validate_opaque_timing(mutated)

    def test_CT195_exact_counter_neutral_path_and_two_raw_panels(self):
        derived = ct.derivative(self.original)
        ct.validate_counter_neutral(derived, self.driver)
        self.assertIn(b"ct195_arithmetic_norm_no_counter", derived)
        self.assertIn(b"CT195_EXTRA_PANEL_ADMISSION_RECEIPT", self.driver)
        self.assertEqual(self.driver.count(b"for _ in 0..64 {"), 2)
        self.assertIn(b'"counter_control_slots":counter_control_slots', self.driver)
        self.assertTrue(ct.audit()["source_audit_passed"])

    def test_CT195_reject_non_neutral_math_or_substituted_norm(self):
        d = ct.derivative(self.original)
        original = b"        descend_point(curve::pmul(&target.f, &target.curve, &point, 2))\n    }"
        for replacement in (
            b"        self.norm_point(to, point)\n    }",
            b"        self.bump(|c| c.transported_norm_doubling += 1);\n        descend_point(curve::pmul(&target.f, &target.curve, &point, 2))\n    }",
            b"        descend_point(curve::pmul(&target.f, &target.curve, &point, 3))\n    }",
        ):
            with self.subTest(replacement=replacement):
                altered = d.replace(original, replacement)
                self.assertNotEqual(d, altered)
                with self.assertRaises(ValueError):
                    ct.validate_counter_neutral(altered, self.driver)

    def test_CT195_reject_missing_extra_admission_or_raw_control(self):
        d = ct.derivative(self.original)
        for old, new in (
            (b"CT195_EXTRA_PANEL_ADMISSION_RECEIPT", b"CT192_OWNER_ADMISSION_RECEIPT"),
            (b'extra_admission.trim().is_empty()', b'admission.trim().is_empty()'),
            (b'counter_control_slots.push(json!({', b'slots.push(json!({'),
            (b'"counter_control_slots":counter_control_slots', b'"counter_control_slots":[]'),
            (b'expected.transported_norm_doubling += 1;', b'expected.transported_norm_doubling += 2;'),
            (b'let measured_operand = black_box(point);', b'let measured_operand = point;'),
        ):
            with self.subTest(old=old):
                altered = self.driver.replace(old, new)
                self.assertNotEqual(self.driver, altered)
                with self.assertRaises(ValueError):
                    ct.validate_counter_neutral(d, altered)

if __name__ == "__main__":
    main()

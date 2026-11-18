#!/usr/bin/env python3
"""CT191 source-only invariants and sabotage controls. No Rust execution."""
import unittest
import source_contract as guard

class CT191SourceGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old, cls.new, cls.runtime, cls.cargo = guard.read_inputs()

    def test_source_exact_and_fail_closed(self):
        result = guard.audit(self.old, self.new, self.runtime, self.cargo)
        self.assertTrue(result["source_guard_passed"])
        self.assertFalse(result["rust_native_executed"])
        self.assertFalse(result["complete_single_target_ecdlp_advantage_established"])

    def test_historical_ct126_blob_is_exact(self):
        self.assertEqual(guard.git_blob(self.old), guard.ORIGINAL_BLOB)

    def test_runtime_blob_is_exact(self):
        self.assertEqual(guard.git_blob(self.runtime), guard.RUNTIME_BLOB)

    def test_denies_surrogate_norm_padd_in_timed_arm(self):
        changed = self.new.replace(
            b"let doubled = curve::pmul(&target.quadratic.f, e, &final_pts[i], 2);",
            b"let doubled = curve::padd(&target.quadratic.f, e, &final_pts[i], &final_pts[i]);")
        self.assertNotEqual(changed, self.new)
        with self.assertRaises(ValueError):
            guard.audit(self.old, changed, self.runtime, self.cargo)

    def test_denies_silent_d_padd_relabelling(self):
        changed = self.new.replace(b'"D_padd","N2_actual"', b'"N2_actual","D_padd"')
        self.assertNotEqual(changed, self.new)
        with self.assertRaises(ValueError):
            guard.audit(self.old, changed, self.runtime, self.cargo)

    def test_denies_historical_original_edit(self):
        changed = self.old.replace(b'curve::padd', b'curve::pmul', 1)
        self.assertNotEqual(changed, self.old)
        with self.assertRaises(ValueError):
            guard.audit(changed, self.new, self.runtime, self.cargo)

    def test_denies_runtime_norm_change(self):
        changed = self.runtime.replace(
            b'descend_point(curve::pmul(&target.f, &target.curve, &point, 2))',
            b'descend_point(curve::padd(&target.f, &target.curve, &point, &point))')
        self.assertNotEqual(changed, self.runtime)
        with self.assertRaises(ValueError):
            guard.audit(self.old, self.new, changed, self.cargo)

    def test_denies_dependency_change(self):
        changed = self.cargo.replace(b"chained-n4-paired-fourth-preflight",
                                     b"chained-n4-paired-fourth-proxy")
        self.assertNotEqual(changed, self.cargo)
        with self.assertRaises(ValueError):
            guard.audit(self.old, self.new, self.runtime, changed)

    def test_denies_missing_new_arm(self):
        changed = self.new.replace(b'5 | 6 => {', b'4 | 5 => {')
        self.assertNotEqual(changed, self.new)
        with self.assertRaises(ValueError):
            guard.audit(self.old, changed, self.runtime, self.cargo)

    def test_no_native_toolchain_in_source_guard(self):
        import inspect
        source = inspect.getsource(guard.audit)
        for forbidden in ("subprocess.run(", "subprocess.Popen(", "os.system("):
            self.assertNotIn(forbidden, source)

if __name__ == "__main__":
    unittest.main()

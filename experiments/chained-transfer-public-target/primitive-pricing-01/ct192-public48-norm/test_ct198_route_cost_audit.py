"""CT198 sabotage/positive controls over the *actual frozen fixture* (source-only)."""
import copy
import json
import unittest
import source_contract as source
import ct198_route_cost_audit as audit

class CounterIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_bytes = source.FROZEN.read_bytes()
        source.validate_fixture(cls.source_bytes)
        cls.rows = json.loads(cls.source_bytes)["all48"]

    def test_real_pinned_fixture_48_route_counts(self):
        result, sha = audit.audited_original()
        self.assertEqual(len(sha), 64)
        self.assertEqual(result["packets"], 48)
        self.assertEqual(result["class_counts"], {"identity": 8, "generic": 40})
        self.assertFalse(result["route_wall_time_measured"])
        self.assertFalse(result["complete_single_target_ecdlp_solved"])
        totals = result["per_route_total_48"]
        d, s, r = [totals[k] for k in audit.ARMS]
        self.assertEqual((d[audit.C169], d[audit.C13], d[audit.N2]), (48, 0, 48))
        self.assertEqual((s[audit.C169], s[audit.C13], s[audit.N2]), (0, 96, 96))
        self.assertEqual((r[audit.C169], r[audit.C13], r[audit.N2]), (0, 96, 48))
        self.assertEqual(r["generic_halving_factorization"], 40)
        self.assertEqual(s["generic_halving_factorization"], 80)
        self.assertEqual(result["per_class_total"]["identity"][audit.ARMS[2]][audit.N2], 8)
        self.assertEqual(result["per_class_total"]["generic"][audit.ARMS[2]][audit.N2], 40)

    def test_exact_only_two_route_differences(self):
        result = audit.audit_rows(self.rows)
        diff = result["retained_minus_direct_48"]
        self.assertEqual(diff[audit.C169], -48)
        self.assertEqual(diff[audit.C13], 96)
        self.assertTrue(all(v == 0 for k, v in diff.items()
                            if k not in (audit.C169, audit.C13)))
        penalty = result["sequential_minus_retained_48"]
        self.assertEqual(penalty[audit.C13], 0)
        self.assertEqual(penalty[audit.C169], 0)
        self.assertEqual(penalty[audit.N2], 48)
        self.assertEqual(penalty["generic_halving_factorization"], 40)
        self.assertEqual(penalty["explicit_half_check"], 352)
        self.assertTrue(all(v >= 0 for v in penalty.values()))

    def test_mutations_of_route_norm_and_C169_are_rejected(self):
        for arm, key, value in (
            (audit.ARMS[0], audit.N2, 2),
            (audit.ARMS[2], audit.C13, 1),
            (audit.ARMS[0], audit.C169, 0),
            (audit.ARMS[2], "external_full_order", 2),
            (audit.ARMS[1], audit.N2, 0),
            (audit.ARMS[1], "explicit_half_check", 0),
        ):
            with self.subTest(arm=arm, key=key):
                tampered = copy.deepcopy(self.rows)
                tampered[0][arm][key] = value
                with self.assertRaises(audit.CounterAuditError):
                    audit.audit_rows(tampered)

    def test_lost_swapped_or_duplicate_cohort_rejected(self):
        for mode in ("pop", "duplicate", "swap"):
            with self.subTest(mode=mode):
                changed = copy.deepcopy(self.rows)
                if mode == "pop":
                    changed.pop()
                elif mode == "duplicate":
                    changed[-1] = copy.deepcopy(changed[0])
                else:
                    changed[0]["scalar_OUTSIDE_runtime"] = 3
                with self.assertRaises(audit.CounterAuditError):
                    audit.audit_rows(changed)

    def test_fixture_blob_mutation_fails_original_pin(self):
        corrupted = self.source_bytes.replace(b'"all48"', b'"broken"', 1)
        self.assertNotEqual(self.source_bytes, corrupted)
        with self.assertRaises(ValueError):
            source.validate_fixture(corrupted)

    def test_boolean_and_negative_counter_rejected(self):
        for bad in (True, -1, 1.5):
            with self.subTest(bad=bad):
                corrupted = copy.deepcopy(self.rows)
                corrupted[0][audit.ARMS[2]][audit.N2] = bad
                with self.assertRaises(audit.CounterAuditError):
                    audit.audit_rows(corrupted)

if __name__ == "__main__":
    unittest.main()

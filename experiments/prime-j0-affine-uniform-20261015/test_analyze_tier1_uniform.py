import unittest

from analyze_tier1_uniform_v2 import paired_speedups, qualifies


class AuditContractTests(unittest.TestCase):
    def setUp(self):
        self.runs = [
            {'serial': 1, 'status': 'valid', 'variant': 'reference',
             'case': 'compare', 'repeat': 0, 'online_ms': 4.0},
            {'serial': 2, 'status': 'valid', 'variant': 'candidate',
             'case': 'compare', 'repeat': 0, 'online_ms': 2.0},
        ]
        self.pairs = [
            {'status': 'valid', 'issues': [], 'case': 'compare', 'repeat': 0,
             'run_serials': {'reference': 1, 'candidate': 2}, 'speedup': 2.0},
        ]

    def test_failed_aa_rejects_interval_below_one(self):
        self.assertFalse(qualifies([{'repeat': 0}], [0.7, 0.9]))

    def test_passing_aa_accepts_interval_above_one(self):
        self.assertTrue(qualifies([], [1.1, 1.2]))

    def test_pair_ratio_is_recomputed_from_raw_arms(self):
        self.assertEqual(paired_speedups(self.runs, self.pairs, ['compare'], 1),
                         {(0, 'compare'): 2.0})

    def test_tampered_pair_speedup_is_rejected(self):
        self.pairs[0]['speedup'] = 1.5
        with self.assertRaises(AssertionError):
            paired_speedups(self.runs, self.pairs, ['compare'], 1)

    def test_mismatched_raw_serial_mapping_is_rejected(self):
        self.pairs[0]['run_serials'] = {'reference': 2, 'candidate': 1}
        with self.assertRaises(AssertionError):
            paired_speedups(self.runs, self.pairs, ['compare'], 1)


if __name__ == '__main__':
    unittest.main()

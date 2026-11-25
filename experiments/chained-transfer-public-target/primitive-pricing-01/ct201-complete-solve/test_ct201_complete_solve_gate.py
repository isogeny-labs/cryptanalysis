"""Synthetic protocol contract controls only; none are native timings."""
import copy
import unittest
from ct201_complete_solve_gate import evaluate, digest_input, prime64

C = {'p': 97, 'a': 1, 'b': 1, 'r': 97, 'G': [0, 1], 'Q': [75, 1]}
N = {'setup', 'transfer', 'relation_collection', 'linear_algebra',
     'individual_log', 'verification', 'other'}


def evidence(candidate=8_000, base=12_000, sham=12_000):
    rows = []
    for block in range(8):
        for arm in ('transfer', 'rho', 'rho_sham', 'bsgs', 'ic'):
            ns = (candidate if arm == 'transfer' else
                  base if arm == 'rho' else
                  sham if arm == 'rho_sham' else
                  base+1_000 if arm == 'bsgs' else base+2_000)
            rows.append({'block': block, 'arm': arm, 'solution': 7,
                         'input_sha256': digest_input(C),
                         'stdout_sha256': 'a'*64, 'binary_sha256': 'b'*64,
                         'host_id': 'example', 'cold_process': True,
                         'external_wall_ns': ns, 'peak_rss_kib': 500,
                         'phases_ns': {k: 100 for k in N}})
    return {'schema': 'ct201/full-cold-evidence/v1', 'curve': C,
            'memory_cap_kib': 1024, 'runs': rows}


class ContractTests(unittest.TestCase):
    def test_synthetic_positive(self):
        result = evaluate(evidence())
        self.assertEqual(result['outcome'], 'candidate_needs_external_signed_verifier')
        self.assertAlmostEqual(result['candidate_ratio_geomean'], 1.5)
        self.assertEqual(result['complete_pair_count'], 8)
        self.assertEqual(result['standing'], '[pcc:unverified]')
        self.assertTrue(result['untrusted_execution_receipts'])

    def test_synthetic_negative(self):
        self.assertEqual(evaluate(evidence(candidate=15_000))['outcome'], 'no_qualified_advantage')

    def test_synthetic_bad_aa(self):
        self.assertEqual(evaluate(evidence(sham=9_000))['outcome'], 'no_qualified_advantage')

    def test_primality_64bit_boundary(self):
        self.assertTrue(prime64(2**61 - 1))
        self.assertFalse(prime64(341550071728321))
        with self.assertRaises(ValueError): prime64(2**64 + 13)

    def test_reject_scalar_tampering(self):
        d = evidence(); d['runs'][0]['solution'] = 8
        with self.assertRaisesRegex(ValueError, 'wrong public-target'): evaluate(d)

    def test_reject_point_tampering(self):
        d = evidence(); d['curve'] = {**C, 'Q': [75, 2]}
        with self.assertRaises(ValueError): evaluate(d)

    def test_reject_false_prime(self):
        d = evidence(); d['curve'] = {**C, 'p': 91}
        with self.assertRaisesRegex(ValueError, 'prime subgroup'): evaluate(d)

    def test_reject_boolean_time(self):
        d = evidence(); d['runs'][0]['external_wall_ns'] = True
        with self.assertRaises(ValueError): evaluate(d)

    def test_reject_missing_phase(self):
        d = evidence(); del d['runs'][0]['phases_ns']['linear_algebra']
        with self.assertRaisesRegex(ValueError, 'missing phase'): evaluate(d)

    def test_reject_duplicate(self):
        d = evidence(); d['runs'].append(copy.deepcopy(d['runs'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate arm'): evaluate(d)

    def test_reject_omitted_baseline(self):
        d = evidence(); d['runs'] = [v for v in d['runs'] if not (v['block']==3 and v['arm']=='ic')]
        with self.assertRaisesRegex(ValueError, 'missing matched'): evaluate(d)

    def test_reject_warm(self):
        d = evidence(); d['runs'][0]['cold_process'] = False
        with self.assertRaisesRegex(ValueError, 'fresh process'): evaluate(d)

    def test_reject_mismatched_host(self):
        d = evidence(); d['runs'][0]['host_id'] = 'different'
        with self.assertRaisesRegex(ValueError, 'single host'): evaluate(d)

    def test_reject_mismatched_input(self):
        d = evidence(); d['runs'][0]['input_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'input digest'): evaluate(d)

    def test_reject_invalid_receipt(self):
        d = evidence(); d['runs'][0]['stdout_sha256'] = 'h'*64
        with self.assertRaisesRegex(ValueError, 'stdout_sha256'): evaluate(d)

    def test_reject_memory_cap(self):
        d = evidence(); d['runs'][0]['peak_rss_kib'] = 999_999
        with self.assertRaisesRegex(ValueError, 'memory cap'): evaluate(d)

    def test_reject_phase_sum_over_wall(self):
        d = evidence(); d['runs'][0]['phases_ns']['setup'] = 100_000
        with self.assertRaisesRegex(ValueError, 'exceeds process wall'): evaluate(d)

    def test_reject_short_panel(self):
        d = evidence(); d['runs'] = [v for v in d['runs'] if v['block'] < 7]
        with self.assertRaisesRegex(ValueError, 'eight'): evaluate(d)

    def test_reject_extra_field(self):
        d = evidence(); d['runs'][0]['self_verified'] = True
        with self.assertRaisesRegex(ValueError, 'schema mismatch'): evaluate(d)

    def test_reject_invalid_G_order(self):
        d = evidence(); d['curve'] = {**C, 'r': 89}
        with self.assertRaisesRegex(ValueError, 'G not in'): evaluate(d)


if __name__ == '__main__':
    unittest.main()

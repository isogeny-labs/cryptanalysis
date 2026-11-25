"""CT203 synthetic honest-curve and sabotage controls. No native ECDLP timings."""
import copy
import unittest

from ct201_complete_solve_gate import digest_input, mul
from ct202_balanced_order_gate import ROSTER
from ct203_fresh_target_gate import SCHEMA, audit, canonical_sha

BASE = {'p': 97, 'a': 1, 'b': 1, 'r': 97, 'G': [0, 1]}
PHASES = ('setup', 'transfer', 'relation_collection', 'linear_algebra',
          'individual_log', 'verification', 'other')


def fixture(cycles=1, candidate=8000, baseline=12000):
    points = []
    runs = []
    for j in range(10*cycles):
        scalar = 17 + j
        Q = list(mul(tuple(BASE['G']), scalar, BASE['p'], BASE['a']))
        points.append({'block': j, 'Q': Q})
        instance = {**BASE, 'Q': Q}
        for arm in ROSTER[j % 10]:
            wall = candidate if arm == 'transfer' else baseline
            runs.append({
                'block': j, 'arm': arm, 'solution': scalar,
                'input_sha256': digest_input(instance),
                'stdout_sha256': 'a'*64,
                'binary_sha256': 'b'*64,
                'host_id': 'synthetic-only',
                'cold_process': True, 'external_wall_ns': wall,
                'peak_rss_kib': 500,
                'phases_ns': {x: 100 for x in PHASES},
            })
    return {
        'schema': SCHEMA, 'curve': copy.deepcopy(BASE),
        'memory_cap_kib': 1024,
        'target_roster': points,
        'target_roster_sha256': canonical_sha(points),
        'runs': runs,
    }


class CT203Tests(unittest.TestCase):
    def test_positive_nonclaiming_distinct_targets(self):
        res = audit(fixture())
        self.assertEqual(res['distinct_target_classes'], 10)
        self.assertEqual(res['complete_williams_cycles'], 1)
        self.assertAlmostEqual(res['candidate_ratio_geomean'], 1.5)
        self.assertEqual(res['standing'], '[pcc:unverified]')
        self.assertEqual(res['outcome'], 'candidate_needs_external_signed_verifier')
        self.assertTrue(res['cold_executions_and_blind_challenge_generation_unattested'])

    def test_slower_no_advantage(self):
        self.assertEqual(audit(fixture(candidate=18000))['outcome'],
                         'no_qualified_advantage')

    def test_one_fixed_scalar_fails_even_if_each_is_a_valid_scalar(self):
        d = fixture()
        for row in d['runs'][5:10]:
            row['solution'] = 17
        with self.assertRaisesRegex(ValueError, 'wrong public-target'):
            audit(d)

    def test_reject_exact_duplicate_target(self):
        d = fixture()
        d['target_roster'][1]['Q'] = d['target_roster'][0]['Q'][:]
        d['target_roster_sha256'] = canonical_sha(d['target_roster'])
        with self.assertRaisesRegex(ValueError, 'repeated target'):
            audit(d)

    def test_reject_inverse_duplicate_target(self):
        d = fixture()
        x, y = d['target_roster'][0]['Q']
        d['target_roster'][1]['Q'] = [x, (-y) % BASE['p']]
        d['target_roster_sha256'] = canonical_sha(d['target_roster'])
        with self.assertRaisesRegex(ValueError, 'repeated target'):
            audit(d)

    def test_reject_false_roster_digest(self):
        d = fixture()
        d['target_roster_sha256'] = 'f'*64
        with self.assertRaisesRegex(ValueError, 'roster digest mismatch'):
            audit(d)

    def test_reject_per_target_input_digest_mismatch(self):
        d = fixture()
        d['runs'][5]['input_sha256'] = d['runs'][0]['input_sha256']
        with self.assertRaisesRegex(ValueError, 'per-target input digest'):
            audit(d)

    def test_reject_partial_cycle(self):
        d = fixture()
        d['target_roster'] = d['target_roster'][:9]
        d['target_roster_sha256'] = canonical_sha(d['target_roster'])
        d['runs'] = d['runs'][:45]
        with self.assertRaisesRegex(ValueError, 'complete 10-block'):
            audit(d)

    def test_reject_reranked_arms(self):
        d = fixture()
        d['runs'][0], d['runs'][1] = d['runs'][1], d['runs'][0]
        with self.assertRaisesRegex(ValueError, 'chronological Williams'):
            audit(d)

    def test_reject_sham_binary(self):
        d = fixture()
        for row in d['runs']:
            if row['arm'] == 'rho_sham':
                row['binary_sha256'] = 'd'*64
        with self.assertRaisesRegex(ValueError, 'identical executable'):
            audit(d)

    def test_reject_candidate_binary_drift(self):
        d = fixture()
        positions = [i for i, row in enumerate(d['runs'])
                     if row['arm'] == 'transfer']
        d['runs'][positions[2]]['binary_sha256'] = 'd'*64
        with self.assertRaisesRegex(ValueError, 'executable drift'):
            audit(d)

    def test_reject_bad_scalar(self):
        d = fixture()
        d['runs'][0]['solution'] += 1
        with self.assertRaisesRegex(ValueError, 'wrong public-target'):
            audit(d)

    def test_reject_invalid_memory_or_phase(self):
        d = fixture()
        d['runs'][0]['peak_rss_kib'] = 2000
        with self.assertRaisesRegex(ValueError, 'memory cap'):
            audit(d)
        d = fixture()
        d['runs'][0]['phases_ns']['transfer'] = 100000
        with self.assertRaisesRegex(ValueError, 'phase sum exceeds'):
            audit(d)

    def test_reject_invalid_field_or_subgroup(self):
        d = fixture()
        d['curve']['p'] = 91
        with self.assertRaisesRegex(ValueError, 'must be prime'):
            audit(d)
        d = fixture()
        d['curve']['r'] = 89
        with self.assertRaisesRegex(ValueError, 'not of declared prime order'):
            audit(d)

    def test_reject_boolean_and_warm(self):
        d = fixture()
        d['runs'][0]['external_wall_ns'] = True
        with self.assertRaises(ValueError):
            audit(d)
        d = fixture()
        d['runs'][0]['cold_process'] = False
        with self.assertRaisesRegex(ValueError, 'warm/non-cold'):
            audit(d)

    def test_two_cycles_remain_distinct(self):
        d = fixture(cycles=2)
        v = audit(d)
        self.assertEqual(v['complete_williams_cycles'], 2)
        self.assertEqual(v['distinct_target_classes'], 20)


if __name__ == '__main__':
    unittest.main()

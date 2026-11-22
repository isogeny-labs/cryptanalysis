"""Synthetic CT202 ordering/identical-binary contract tests; no native timing."""
import collections
import copy
import unittest

from ct201_complete_solve_gate import evaluate
from ct202_balanced_order_gate import ARMS, ROSTER, audit
from test_ct201_complete_solve_gate import evidence


def balanced():
    source = evidence()
    by_arm = {row['arm']: copy.deepcopy(row) for row in source['runs'][:5]}
    source['runs'] = []
    for block in range(10):
        for arm in ROSTER[block]:
            row = copy.deepcopy(by_arm[arm])
            row['block'] = block
            source['runs'].append(row)
    return source


class CT202Tests(unittest.TestCase):
    def test_williams_position_and_carryover_balance(self):
        self.assertEqual(len(ROSTER), 10)
        self.assertTrue(all(set(row) == set(ARMS) for row in ROSTER))
        positions = collections.Counter((pos, arm) for row in ROSTER
                                        for pos, arm in enumerate(row))
        pairs = collections.Counter((row[i-1], row[i]) for row in ROSTER
                                    for i in range(1, 5))
        self.assertEqual(len(positions), 25)
        self.assertEqual(set(positions.values()), {2})
        self.assertEqual(len(pairs), 20)
        self.assertEqual(set(pairs.values()), {2})

    def test_toy_positive_stays_unverified(self):
        value = audit(balanced())
        self.assertEqual(value['complete_pair_count'], 10)
        self.assertEqual(value['standing'], '[pcc:unverified]')
        self.assertEqual(value['outcome'], 'candidate_needs_external_signed_verifier')
        self.assertEqual(value['ct202_order_and_binary_binding']['complete_williams_cycles'], 1)

    def test_reject_candidate_always_last_order_confounded(self):
        d = balanced()
        d['runs'] = [r for block in range(10)
                     for r in sorted(d['runs'][5*block:5*(block+1)],
                                     key=lambda v: v['arm'] == 'transfer')]
        self.assertEqual(evaluate(d)['complete_pair_count'], 10)
        with self.assertRaisesRegex(ValueError, 'chronological roster'):
            audit(d)

    def test_reject_sham_substitute_with_same_fake_timing(self):
        d = balanced()
        for row in d['runs']:
            if row['arm'] == 'rho_sham':
                row['binary_sha256'] = 'c'*64
        self.assertTrue(evaluate(d)['aa_within_preregistered_10pct'])
        with self.assertRaisesRegex(ValueError, 'identical executable'):
            audit(d)

    def test_reject_candidate_binary_drift(self):
        d = balanced()
        d['runs'][0]['binary_sha256'] = 'd'*64
        self.assertEqual(evaluate(d)['complete_pair_count'], 10)
        with self.assertRaisesRegex(ValueError, 'executable changed'):
            audit(d)

    def test_reject_partial_cycle_not_cherry_pick(self):
        d = balanced()
        d['runs'] = d['runs'][:45]
        self.assertEqual(evaluate(d)['complete_pair_count'], 9)
        with self.assertRaisesRegex(ValueError, 'complete 10-block'):
            audit(d)

    def test_reject_reversed_block_order(self):
        d = balanced()
        d['runs'] = d['runs'][5:10] + d['runs'][:5] + d['runs'][10:]
        self.assertEqual(evaluate(d)['complete_pair_count'], 10)
        with self.assertRaisesRegex(ValueError, 'chronological roster'):
            audit(d)

    def test_accept_two_whole_cycles(self):
        d = balanced()
        repeated = copy.deepcopy(d['runs'])
        for row in repeated:
            row['block'] += 10
        d['runs'] += repeated
        self.assertEqual(audit(d)['ct202_order_and_binary_binding']['complete_williams_cycles'], 2)


if __name__ == '__main__':
    unittest.main()

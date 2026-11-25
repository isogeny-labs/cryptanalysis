"""The planted arm's comparison (n2x_compare.py) and the native trace, against a pure-Python
model of tau.sage (tests/model_sage.py), with planted corruptions. No Sage, no timing.

    N19_LIB=PATH/libtau6loop.so python3 -m unittest -v tests/test_n2x_compare.py
"""
import copy
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, EXP)
sys.path.insert(0, HERE)
import n2x_compare as nc  # noqa: E402
import model_sage as ms  # noqa: E402

LIB = os.environ.get('N19_LIB')
PANEL = json.load(open(os.path.join(EXP, 'inputs', 'panel.json')))


def canonical(rel):
    return [[int(c), int(s), int(e)] for c, s, e in rel]


def model_run(scalar, seed):
    cur = ms.Cur(LIB)
    P = ms.generator()
    Q = ms.B.mul(scalar, P)
    log, rels = [], []
    rng = nc.RecRandom(seed)
    st = ms.tau_dlp(cur, P, Q, rng, nc.tracing_relation(ms.tau_relation, cur.enc, log, rels, canonical))
    return cur, P, Q, st, rng, log, rels


def compare_all(nat, cur, P, Q, st, rng, log, rels):
    out = nc.compare_setup(nat, list(P), [list(r) for r in cur.reps],
                           [[x, v[0][0], v[0][1], v[1], v[2], v[3]] for x, v in cur.base.items()], st['lambda'],
                           list(Q))
    targets = nc.assemble_targets(rng.calls, log)
    counts = {f: st[f] for f in ('targets', 'gb_calls', 'spurious', 'relations', 'log')}
    out.update(nc.compare_targets(nat, targets, counts, st['recovered'], [canonical(r) for r in rels]))
    rows, rhs, used = nc.rows_and_rhs(targets, st['lambda'], ms.P_ORD, ms.H)
    out.update(nc.compare_kernel(nat, used, st['basis'], st['kernel_index'], st['log']))
    return out


@unittest.skipUnless(LIB, 'set N19_LIB to the built libtau6loop.so')
class Compare(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pt = PANEL['smoke_points'][0]
        cls.pt = pt
        cls.model = model_run(pt['scalar'], pt['rng_seed'])
        cls.nat = ms.native_trace(LIB, pt['scalar'], pt['rng_seed'])

    def test_rec_random_is_the_same_stream(self):
        import random
        a, b = random.Random('x:1'), nc.RecRandom('x:1')
        v1, v2 = list(range(19)), list(range(19))
        for _ in range(200):
            self.assertEqual(a.randrange(1, 130873), b.randrange(1, 130873))
            a.shuffle(v1)
            b.shuffle(v2)
            self.assertEqual(v1, v2)
        self.assertIs(nc.RecRandom._randbelow, random.Random._randbelow)

    def test_model_equals_native_on_every_item(self):
        out = compare_all(self.nat, *self.model)
        st = self.model[3]
        self.assertEqual(out['checked_targets'], st['targets'])
        self.assertEqual(out['checked_calls'], st['gb_calls'])
        self.assertEqual(out['checked_relations'], st['relations'])
        self.assertEqual(out['checked_reps'], 29)
        self.assertEqual(out['checked_base_entries'], 33)
        self.assertGreater(out['kernel_dimension'], 0)
        self.assertEqual(st['log'], self.pt['scalar'] % ms.P_ORD)

    def corrupt(self, fn):
        nat = copy.deepcopy(self.nat)
        fn(nat)
        with self.assertRaises(nc.Mismatch):
            compare_all(nat, *self.model)

    def test_planted_corruptions_fail(self):
        def target_shift(n):
            n['targets'][5][3] = n['targets'][5][3][1:] + n['targets'][5][3][:1]

        def target_rel(n):
            t = next(t for t in n['targets'] if t[5] is not None)
            t[5][0][1] *= -1

        def kernel(n):
            n['kernel_basis'][0][-1] = (n['kernel_basis'][0][-1] + 1) % ms.P_ORD

        def rep(n):
            n['setup']['reps'][3] = [n['setup']['reps'][3][0], n['setup']['reps'][3][0] ^ n['setup']['reps'][3][1]]

        def calls(n):
            n['targets'][2][4] += 1

        for fn in (target_shift, target_rel, kernel, rep, calls,
                   lambda n: n['counts'].__setitem__('spurious', n['counts']['spurious'] + 1),
                   lambda n: n.__setitem__('kernel_index', (n['kernel_index'] or 0) + 1),
                   lambda n: n['targets'].pop(),
                   lambda n: n['setup']['base'].pop(),
                   lambda n: n.__setitem__('lambda', 1)):
            self.corrupt(fn)

    def test_second_smoke_point_and_an_archived_instance(self):
        for scalar, seed in ((PANEL['smoke_points'][1]['scalar'], PANEL['smoke_points'][1]['rng_seed']),
                             (2003, 'tau:tau6:0')):
            m = model_run(scalar, seed)
            out = compare_all(ms.native_trace(LIB, scalar, seed), *m)
            self.assertEqual(out['checked_targets'], m[3]['targets'])


if __name__ == '__main__':
    unittest.main()

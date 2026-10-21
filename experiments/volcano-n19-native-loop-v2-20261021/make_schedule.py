"""Frozen run order (schedule.json) for volcano-n19-native-loop-v2-20261021.

    python3 make_schedule.py           write schedule.json
    python3 make_schedule.py --check   regenerate and compare (CI, the runner and the verifier)

Two parts, each with its own serials:

* `smoke` (untimed gate, its own workflow job, before the timed job): S0 (the v3 selftest
  arm on libtau6loop.so's tau6_* solve), S0b (the tau6dlp binary's compiled solve on every
  S0 system), O1 (baseline N on the ten archived scalars), O2 (N2 on them), then the two
  smoke points (v3 panel p00 and p01, archived Sage rows in run 39387473809), each through
  B, N, N2, N2aa, N2X, rho and a warm N2 once. Correctness only; its times are never used.
* `timed`: S0, S0b, O1, O2, then Q01..Q24, one segment per held-out point
  (inputs/panel.json). Point i's generator is
  random.Random('volcano-n19-native-loop-v2-20261021:order:%d' % i), drawing in this order:
  1. the start of the primary block (N or N2);
  2. the start of the A/A block (N2 or N2aa);
  3. the start of the planted block (N2X or N2);
  4. the order of the six sub-blocks (primary, aa, planted, B, rho, warm), by shuffle.
  The primary block is 2K processes in strict alternation (N N2 N N2 ... or N2 N N2 N ...),
  pair j = positions 2j-2 and 2j-1; the A/A block is 2K_AA processes alternating N2 and
  N2aa; the planted block is one pair of N2X and N2; B, rho and warm are one process each
  (warm = one N2 process with --warm: the repeated-batch secondary, kept out of every pair so
  no paired process carries post-interval batch work). Every IC process of a point uses the
  point's rng seed.

Every run carries `role` (s0, s0b, o1, o2, primary, aa, planted, b, rho, warm, smoke), `pair`,
`side` and `position`; the verifier reads them from here.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXPERIMENT = 'volcano-n19-native-loop-v2-20261021'
K, K_AA, K_PLANT = 5, 3, 1
ORDER_SEED = 'volcano-n19-native-loop-v2-20261021:order:%d'
SMOKE_ARMS = ('B', 'N', 'N2', 'N2aa', 'N2X', 'rho', 'N2')


def alternate(first, second, start, pairs):
    other = second if start == first else first
    return [start if n % 2 == 0 else other for n in range(2 * pairs)]


def pt_fields(pt):
    return {'point': pt['id'], 'scalar': pt['scalar'], 'rng_seed': pt['rng_seed']}


def gate(sid, arm, role):
    return {'id': sid, 'kind': 'gate', 'runs': [{'arm': arm, 'role': role, 'point': None, 'warm': False,
                                                  'pair': None, 'side': None, 'position': None}]}


def gates_segments():
    return [gate('S0', 'selftest', 's0'), gate('S0b', 'S0b', 's0b'), gate('O1', 'O', 'o1'), gate('O2', 'O2', 'o2')]


def number(segments):
    serial = 0
    for seg in segments:
        for r in seg['runs']:
            serial += 1
            r['serial'] = serial
    return serial


def build():
    panel = json.load(open(os.path.join(HERE, 'inputs', 'panel.json')))
    smoke = gates_segments()
    for pt in panel['smoke_points']:
        runs = []
        for n, a in enumerate(SMOKE_ARMS):
            warm = n == len(SMOKE_ARMS) - 1
            runs.append(dict(arm=a, role='warm' if warm else 'smoke', pair=None, side=a, position=n, warm=warm,
                             **pt_fields(pt)))
        smoke.append({'id': 'SM-' + pt['id'], 'kind': 'smoke_point', 'point': pt['id'], 'runs': runs})
    timed = gates_segments()
    for i, pt in enumerate(panel['points']):
        rng = random.Random(ORDER_SEED % i)
        start_primary = rng.choice(['N', 'N2'])
        start_aa = rng.choice(['N2', 'N2aa'])
        start_plant = rng.choice(['N2X', 'N2'])
        order = ['primary', 'aa', 'planted', 'b', 'rho', 'warm']
        rng.shuffle(order)
        blocks = {k: [] for k in order}
        for name, first, second, start, pairs in (('primary', 'N', 'N2', start_primary, K),
                                                  ('aa', 'N2', 'N2aa', start_aa, K_AA),
                                                  ('planted', 'N2X', 'N2', start_plant, K_PLANT)):
            for pos, arm in enumerate(alternate(first, second, start, pairs)):
                blocks[name].append(dict(arm=arm, role=name, pair=pos // 2 + 1, side=arm, position=pos, warm=False,
                                         **pt_fields(pt)))
        for name, arm, warm in (('b', 'B', False), ('rho', 'rho', False), ('warm', 'N2', True)):
            blocks[name].append(dict(arm=arm, role=name, pair=None, side=None, position=0, warm=warm,
                                     **pt_fields(pt)))
        timed.append({'id': 'Q%02d' % (i + 1), 'kind': 'point', 'point': pt['id'],
                      'starts': {'primary': start_primary, 'aa': start_aa, 'planted': start_plant},
                      'sub_block_order': order, 'runs': [r for name in order for r in blocks[name]]})
    return {'schema': 1, 'experiment': EXPERIMENT,
            'design': {'primary_pairs_per_point': K, 'aa_pairs_per_point': K_AA, 'planted_pairs_per_point': K_PLANT,
                       'points': len(panel['points']), 'order_seed': ORDER_SEED,
                       'smoke_points': [p['id'] for p in panel['smoke_points']], 'smoke_arms': list(SMOKE_ARMS)},
            'parts': {'smoke': {'segments': smoke, 'runs': number(smoke)},
                      'timed': {'segments': timed, 'runs': number(timed)}}}


def text():
    return json.dumps(build(), indent=1, sort_keys=True) + '\n'


def main():
    path = os.path.join(HERE, 'schedule.json')
    if '--check' in sys.argv:
        if open(path).read() != text():
            raise SystemExit('schedule.json differs from make_schedule.py')
        print('schedule ok')
    else:
        open(path, 'w').write(text())


if __name__ == '__main__':
    main()

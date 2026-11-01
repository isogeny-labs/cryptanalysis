"""Frozen run order (schedule.json) for volcano-n19-native-tau6-v3-20261020 (protocol v3).

    python3 make_schedule.py           write schedule.json
    python3 make_schedule.py --check   regenerate and compare (CI, the runner and the verifier)

Two parts, each with its own serials:

* `smoke` (untimed; the v3 Sage smoke gate, its own workflow job, before the
  timed job): S0, O1, then the two smoke points (v2 panel p00 and p01, with
  v2's rng seeds: the rows that crashed in run 39376405326), each through
  B, N, Naa, NX and rho once. Correctness only; its times are never used.
* `timed`: S0, O1, then P01..P20, one segment per held-out point
  (inputs/panel.json). Point i's generator is
  random.Random('volcano-n19-native-tau6-v3-20261020:order:%d' % i), and it
  draws, in this order:
  1. the start of the primary block (B or N);
  2. the start of the A/A block (N or Naa);
  3. the start of the planted block (NX or N);
  4. the order of the four sub-blocks (primary, aa, planted, rho), by shuffle.
  The primary block is 2K processes in strict alternation (BNBN... or
  NBNB...), pair j = positions 2j-2 and 2j-1. The A/A block is 2K_AA
  processes alternating N and Naa. The planted block is one pair of NX and N.
  The rho block is one rho process. Every IC process of a point uses the
  point's rng seed (the same targets and shift orders in every process).
  The primary N processes (and the smoke N) carry `warm`: after their cold
  interval they run v2's repeated-batch warm measurement (secondary).

Every run carries `role` (s0, o1, primary, aa, planted, rho), `pair`, `side`
and `position` (its index in its block); the verifier reads them from here.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXPERIMENT = 'volcano-n19-native-tau6-v3-20261020'
K, K_AA, K_PLANT = 3, 3, 1
ORDER_SEED = 'volcano-n19-native-tau6-v3-20261020:order:%d'
SMOKE_POINTS = ('p00', 'p01')
SMOKE_ARMS = ('B', 'N', 'Naa', 'NX', 'rho')


def alternate(first, second, start, pairs):
    other = second if start == first else first
    return [start if n % 2 == 0 else other for n in range(2 * pairs)]


def pt_fields(pt):
    return {'point': pt['id'], 'scalar': pt['scalar'], 'rng_seed': pt['rng_seed']}


def gates_segments():
    return [{'id': 'S0', 'kind': 'gate', 'runs': [{'arm': 'selftest', 'role': 's0', 'point': None, 'warm': False,
                                                     'pair': None, 'side': None, 'position': None}]},
            {'id': 'O1', 'kind': 'gate', 'runs': [{'arm': 'O', 'role': 'o1', 'point': None, 'warm': False,
                                                     'pair': None, 'side': None, 'position': None}]}]


def number(segments):
    serial = 0
    for seg in segments:
        for r in seg['runs']:
            serial += 1
            r['serial'] = serial
    return serial


def build():
    panel = json.load(open(os.path.join(HERE, 'inputs', 'panel.json')))
    v2panel = json.load(open(os.path.join(HERE, '..', 'volcano-n19-native-tau6-v2-20261019', 'inputs', 'panel.json')))
    smoke = gates_segments()
    for pid in SMOKE_POINTS:
        pt = next(p for p in v2panel['points'] if p['id'] == pid)
        smoke.append({'id': 'SM-v2' + pid, 'kind': 'smoke_point',
                      'runs': [dict(arm=a, role='smoke', pair=None, side=a, position=n, warm=(a == 'N'),
                                    **pt_fields(pt))
                               for n, a in enumerate(SMOKE_ARMS)]})
    timed = gates_segments()
    for i, pt in enumerate(panel['points']):
        rng = random.Random(ORDER_SEED % i)
        start_primary = rng.choice(['B', 'N'])
        start_aa = rng.choice(['N', 'Naa'])
        start_plant = rng.choice(['NX', 'N'])
        order = ['primary', 'aa', 'planted', 'rho']
        rng.shuffle(order)
        blocks = {'primary': [], 'aa': [], 'planted': [], 'rho': []}
        for name, first, second, start, pairs in (('primary', 'B', 'N', start_primary, K),
                                                  ('aa', 'N', 'Naa', start_aa, K_AA),
                                                  ('planted', 'NX', 'N', start_plant, K_PLANT)):
            for pos, arm in enumerate(alternate(first, second, start, pairs)):
                blocks[name].append(dict(arm=arm, role=name, pair=pos // 2 + 1, side=arm, position=pos,
                                         warm=(name == 'primary' and arm == 'N'), **pt_fields(pt)))
        blocks['rho'].append(dict(arm='rho', role='rho', pair=None, side=None, position=0, warm=False,
                                  **pt_fields(pt)))
        timed.append({'id': 'P%02d' % (i + 1), 'kind': 'point', 'point': pt['id'],
                      'starts': {'primary': start_primary, 'aa': start_aa, 'planted': start_plant},
                      'sub_block_order': order, 'runs': [r for name in order for r in blocks[name]]})
    return {'schema': 3, 'experiment': EXPERIMENT,
            'design': {'primary_pairs_per_point': K, 'aa_pairs_per_point': K_AA, 'planted_pairs_per_point': K_PLANT,
                       'points': len(panel['points']), 'order_seed': ORDER_SEED,
                       'smoke_points': ['v2:' + p for p in SMOKE_POINTS], 'smoke_arms': list(SMOKE_ARMS)},
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

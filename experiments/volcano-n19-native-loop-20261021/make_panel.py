"""Held-out panel for volcano-n19-native-loop-20261021 (role n19-native-loop-heldout).

    python3 make_panel.py           write inputs/panel.json
    python3 make_panel.py --check   regenerate and compare (CI, the runner and the verifier)

24 new planted scalars in [2, r - 2] from a new seed, excluding the ten archived
volcano-ic scalars, the v1, v2 and v3 panels of volcano-n19-native-tau6 (16 + 16 + 20),
their negatives and every Frobenius image +-lambda^e of any of them (no new target lies
in an excluded target's tau-orbit), and each other's orbits. Each point has its own
tauDlp rng seed string, used by every IC process of the point (B, N, N2, N2aa, N2X), so
all of them draw the same targets and shift orders.

The two smoke points are v3 panel points p00 and p01 with v3's seeds: run 39387473809
archived their Sage rows (B, N, Naa, NX), so the untimed smoke job also checks the new
arms against an archived Sage receipt. They are never timed here.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R, LAM, N = 130873, 41811, 19
ARCHIVED = json.load(open(os.path.join(HERE, '..', 'volcano-ic', 'rho-arm-20261014', 'protocol.json')))['scalars']


def panel_points(rel):
    return json.load(open(os.path.join(HERE, '..', rel, 'inputs', 'panel.json')))['points']


V1 = [p['scalar'] for p in panel_points('volcano-n19-native-tau6-20261019')]
V2 = [p['scalar'] for p in panel_points('volcano-n19-native-tau6-v2-20261019')]
V3_POINTS = panel_points('volcano-n19-native-tau6-v3-20261020')
V3 = [p['scalar'] for p in V3_POINTS]
SEED = 'volcano-n19-native-loop-20261021:panel'
COUNT = 24
SMOKE = ('p00', 'p01')


def orbit(s):
    return {sg * s * pow(LAM, e, R) % R for e in range(N) for sg in (1, -1)}


def build():
    forbidden = set()
    for s in ARCHIVED + V1 + V2 + V3:
        forbidden |= orbit(s)
    rng = random.Random(SEED)
    pts, seen = [], set()
    while len(pts) < COUNT:
        s = rng.randrange(2, R - 1)
        o = orbit(s)
        if s in forbidden or o & seen or o & forbidden:
            continue
        seen |= o
        i = len(pts)
        pts.append({'id': 'q%02d' % i, 'scalar': s, 'rng_seed': 'n19-native-loop:%02d' % i})
    assert not seen & forbidden
    smoke = [dict(p, id='v3' + p['id'], source='volcano-n19-native-tau6-v3-20261020 inputs/panel.json ' + p['id'])
             for p in V3_POINTS if p['id'] in SMOKE]
    return {'role': 'n19-native-loop-heldout', 'seed': SEED, 'r': R, 'lambda': LAM,
            'rule': 'new scalars; none equal to, the negative of, or a Frobenius image (+-lambda^e) of an archived '
                    'volcano-ic scalar, of a v1, v2 or v3 panel scalar, or of another panel scalar',
            'excluded_archived_scalars': ARCHIVED, 'excluded_v1_panel_scalars': V1, 'excluded_v2_panel_scalars': V2,
            'excluded_v3_panel_scalars': V3, 'points': pts, 'smoke_points': smoke}


def main():
    path = os.path.join(HERE, 'inputs', 'panel.json')
    text = json.dumps(build(), indent=1) + '\n'
    if '--check' in sys.argv:
        if open(path).read() != text:
            raise SystemExit('inputs/panel.json differs from make_panel.py')
        print('panel ok')
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'w').write(text)


if __name__ == '__main__':
    main()

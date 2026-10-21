"""Held-out panel for volcano-n19-native-loop-v2-20261021 (role n19-native-loop-v2-heldout).

    python3 make_panel.py           write inputs/panel.json
    python3 make_panel.py --check   regenerate and compare (CI, the runner and the verifier)

24 new planted scalars in [2, r - 2] from a new seed, excluding every earlier n = 19
scalar: the ten archived volcano-ic scalars, the v1, v2 and v3 panels of
volcano-n19-native-tau6 (16 + 16 + 20, smoke points included), v1 tau6's local smoke panel,
and the panel and smoke points of volcano-n19-native-loop-20261021 (24 + 2; a byte copy of
that branch's frozen inputs/panel.json is inputs/excluded/, SHA-256 checked here, because
that experiment may not be on main), their negatives and every Frobenius image +-lambda^e
of any of them (no new target lies in an excluded target's tau-orbit), and each other's
orbits. The per-point rng seed strings are new too (prefix n19-native-loop-v2:). Each point has its own
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
V1_LOCAL = [p['scalar'] for p in json.load(open(os.path.join(
    HERE, '..', 'volcano-n19-native-tau6-20261019', 'smoke', 'local_panel.json')))['points']]
LOOP_V1_FILE = os.path.join(HERE, 'inputs', 'excluded', 'volcano-n19-native-loop-20261021-panel.json')
LOOP_V1_SHA256 = '177eb69534ab58ae02a82daff2d7d8cad92fd60d6b633a9f4d15875990b638a2'  # origin c8a05b59f
_loop_v1 = json.load(open(LOOP_V1_FILE))
LOOP_V1 = [p['scalar'] for p in _loop_v1['points'] + _loop_v1['smoke_points']]
LOOP_V1_SEEDS = [p['rng_seed'] for p in _loop_v1['points'] + _loop_v1['smoke_points']]
SEED = 'volcano-n19-native-loop-v2-20261021:panel'
SEED_PREFIX = 'n19-native-loop-v2:'
COUNT = 24
SMOKE = ('p00', 'p01')


def orbit(s):
    return {sg * s * pow(LAM, e, R) % R for e in range(N) for sg in (1, -1)}


def build():
    forbidden = set()
    import hashlib
    assert hashlib.sha256(open(LOOP_V1_FILE, 'rb').read()).hexdigest() == LOOP_V1_SHA256, LOOP_V1_FILE
    for s in ARCHIVED + V1 + V2 + V3 + V1_LOCAL + LOOP_V1:
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
        pts.append({'id': 'q%02d' % i, 'scalar': s, 'rng_seed': SEED_PREFIX + '%02d' % i})
    assert not seen & forbidden
    assert not {p['rng_seed'] for p in pts} & set(LOOP_V1_SEEDS)
    smoke = [dict(p, id='v3' + p['id'], source='volcano-n19-native-tau6-v3-20261020 inputs/panel.json ' + p['id'])
             for p in V3_POINTS if p['id'] in SMOKE]
    return {'role': 'n19-native-loop-v2-heldout', 'seed': SEED, 'r': R, 'lambda': LAM,
            'rule': 'new scalars; none equal to, the negative of, or a Frobenius image (+-lambda^e) of an archived '
                    'volcano-ic scalar, of a tau6 v1, v2 or v3 panel scalar, of a tau6 v1 local smoke scalar, of a '
                    'volcano-n19-native-loop-20261021 panel or smoke scalar, or of another panel scalar; new rng '
                    'seed strings',
            'excluded_archived_scalars': ARCHIVED, 'excluded_v1_panel_scalars': V1, 'excluded_v2_panel_scalars': V2,
            'excluded_v3_panel_scalars': V3, 'excluded_v1_local_smoke_scalars': V1_LOCAL,
            'excluded_native_loop_v1_scalars': LOOP_V1,
            'excluded_native_loop_v1_panel_sha256': LOOP_V1_SHA256, 'points': pts, 'smoke_points': smoke}


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

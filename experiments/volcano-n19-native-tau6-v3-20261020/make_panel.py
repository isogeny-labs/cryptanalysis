"""Held-out panel for volcano-n19-native-tau6-v3-20261020 (role n19-native-heldout-v3).

    python3 make_panel.py           write inputs/panel.json
    python3 make_panel.py --check   regenerate and compare (CI)

20 new planted scalars in [2, r - 2], drawn from a new seed (v3), excluding
the ten scalars of volcano-ic (run.sage scalars(), seed 20260924, the
rho-arm-20261014 panel), the 16 scalars of the v1 panel and the 16 of the v2
panel (v2 points p00 and p01 are also v3's untimed Sage smoke points), their
negatives, and any scalar whose target is a Frobenius image +-lambda^e Q of
one of them (so no new target lies in an excluded target's tau-orbit). Each
point has its own tauDlp rng seed string, used by every IC process of that
point (so every B, N, Naa and NX process of a point draws the same targets).
The v1 panel was never timed (run 39307409409 stopped at S0); the v2 panel ran
in run 39376405326 but every IC row crashed after its interval, so no v2 IC
timing exists; both are excluded anyway.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R, LAM, N = 130873, 41811, 19
ARCHIVED = json.load(open(os.path.join(HERE, '..', 'volcano-ic', 'rho-arm-20261014', 'protocol.json')))['scalars']


def panel_scalars(rel):
    return [p['scalar'] for p in json.load(open(os.path.join(HERE, '..', rel, 'inputs', 'panel.json')))['points']]


V1_PANEL = panel_scalars('volcano-n19-native-tau6-20261019')
V2_PANEL = panel_scalars('volcano-n19-native-tau6-v2-20261019')
SEED = 'volcano-n19-native-tau6-v3-20261020:panel'
COUNT = 20


def orbit(s):
    return {sg * s * pow(LAM, e, R) % R for e in range(N) for sg in (1, -1)}


def build():
    forbidden = set()
    for s in ARCHIVED + V1_PANEL + V2_PANEL:
        forbidden |= orbit(s)
    rng = random.Random(SEED)
    pts = []
    seen = set()
    while len(pts) < COUNT:
        s = rng.randrange(2, R - 1)
        o = orbit(s)
        if s in forbidden or o & seen:
            continue
        seen |= o
        i = len(pts)
        pts.append({'id': 'p%02d' % i, 'scalar': s, 'rng_seed': 'n19-native-tau6-v3:%02d' % i})
    assert not seen & forbidden
    return {'role': 'n19-native-heldout-v3', 'seed': SEED, 'r': R, 'lambda': LAM,
            'rule': 'new scalars; none equal to, the negative of, or a Frobenius image (+-lambda^e) of an '
                    'archived volcano-ic scalar, of a v1 or v2 panel scalar, or of another panel scalar',
            'excluded_archived_scalars': ARCHIVED, 'excluded_v1_panel_scalars': V1_PANEL,
            'excluded_v2_panel_scalars': V2_PANEL, 'points': pts}


def main():
    path = os.path.join(HERE, 'inputs', 'panel.json')
    text = json.dumps(build(), indent=1) + '\n'
    if '--check' in sys.argv:
        if open(path).read() != text:
            raise SystemExit('inputs/panel.json differs from make_panel.py')
        print('panel ok')
    else:
        open(path, 'w').write(text)


if __name__ == '__main__':
    main()

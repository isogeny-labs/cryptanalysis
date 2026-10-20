"""Held-out panel for volcano-n19-native-tau6-v2-20261019 (role n19-native-heldout-v2).

    python3 make_panel.py           write inputs/panel.json
    python3 make_panel.py --check   regenerate and compare (CI)

16 new planted scalars in [2, r - 2], drawn from a new seed (v2), excluding
the ten scalars of volcano-ic (run.sage scalars(), seed 20260924, the
rho-arm-20261014 panel), the 16 scalars of the v1 panel
(../volcano-n19-native-tau6-20261019/inputs/panel.json, never timed: run
39307409409 stopped at S0), their negatives, and any scalar whose target is a
Frobenius image +-lambda^e Q of one of them (so no new target lies in an
excluded target's tau-orbit). Each point has its own tauDlp rng seed string, used by
every IC arm of that point (so B, N, Naa and NX draw the same targets).
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R, LAM, N = 130873, 41811, 19
ARCHIVED = json.load(open(os.path.join(HERE, '..', 'volcano-ic', 'rho-arm-20261014', 'protocol.json')))['scalars']
V1_PANEL = [p['scalar'] for p in json.load(open(os.path.join(HERE, '..', 'volcano-n19-native-tau6-20261019', 'inputs',
                                                         'panel.json')))['points']]
SEED = 'volcano-n19-native-tau6-v2-20261019:panel'
COUNT = 16


def build():
    forbidden = set()
    for s in ARCHIVED + V1_PANEL:
        for e in range(N):
            for sg in (1, -1):
                forbidden.add(sg * s * pow(LAM, e, R) % R)
    rng = random.Random(SEED)
    pts = []
    seen = set()
    while len(pts) < COUNT:
        s = rng.randrange(2, R - 1)
        orbit = {sg * s * pow(LAM, e, R) % R for e in range(N) for sg in (1, -1)}
        if s in forbidden or orbit & seen:
            continue
        seen |= orbit
        i = len(pts)
        pts.append({'id': 'p%02d' % i, 'scalar': s, 'rng_seed': 'n19-native-tau6-v2:%02d' % i})
    return {'role': 'n19-native-heldout-v2', 'seed': SEED, 'r': R, 'lambda': LAM,
            'rule': 'new scalars; none equal to, the negative of, or a Frobenius image (+-lambda^e) of an '
                    'archived volcano-ic scalar, of a v1 panel scalar, or of another panel scalar',
            'excluded_archived_scalars': ARCHIVED, 'excluded_v1_panel_scalars': V1_PANEL, 'points': pts}


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

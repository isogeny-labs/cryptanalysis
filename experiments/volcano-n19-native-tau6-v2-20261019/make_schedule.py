"""Frozen run order (schedule.json) for volcano-n19-native-tau6-v2-20261019 (protocol v2).

    python3 make_schedule.py           write schedule.json
    python3 make_schedule.py --check   regenerate and compare (CI)

S0: selftest (Sage variety == native == direct S3 on the 7 v1 mismatch systems and 300 new ones; no timing).
O1: the candidate on the ten archived scalars (exactness against run 38520305068; no timing claim).
P00..P15: one segment per held-out point; one fresh process per arm
(B, N, Naa, NX, rho), in the order random.Random('volcano-n19-native-tau6-v2-20261019:order:%d' % i).shuffle
(a new seed; v1 used 2026101919 + i).
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = ['B', 'N', 'Naa', 'NX', 'rho']


def build():
    panel = json.load(open(os.path.join(HERE, 'inputs', 'panel.json')))
    segs = [{'id': 'S0', 'rows': [{'row': 'S0-selftest', 'arm': 'selftest'}]},
            {'id': 'O1', 'rows': [{'row': 'O1-archived', 'arm': 'O'}]}]
    for i, pt in enumerate(panel['points']):
        order = list(ARMS)
        random.Random('volcano-n19-native-tau6-v2-20261019:order:%d' % i).shuffle(order)
        segs.append({'id': 'P%02d' % i, 'point': pt['id'],
                     'rows': [{'row': '%s-%s' % (pt['id'], a), 'arm': a, 'point': pt['id'],
                               'scalar': pt['scalar'], 'rng_seed': pt['rng_seed']} for a in order]})
    return {'experiment': 'volcano-n19-native-tau6-v2-20261019', 'segments': segs,
            'rows': sum(len(s['rows']) for s in segs)}


def main():
    path = os.path.join(HERE, 'schedule.json')
    text = json.dumps(build(), indent=1) + '\n'
    if '--check' in sys.argv:
        if open(path).read() != text:
            raise SystemExit('schedule.json differs from make_schedule.py')
        print('schedule ok')
    else:
        open(path, 'w').write(text)


if __name__ == '__main__':
    main()

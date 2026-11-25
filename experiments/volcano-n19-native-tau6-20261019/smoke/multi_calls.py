"""Local diagnostic: every shift system with two or more solutions that the
candidate meets on the held-out panel and the archived scalars, with the
validity of each solution (in the V' base? a decomposition of R?). Only such
calls could make the order of the variety matter.

    python3 multi_calls.py --lib PATH/libtau6native.so --out multi_calls.json
"""
import argparse
import json
import os
import random

import local_replay as L

ap = argparse.ArgumentParser()
ap.add_argument('--lib', required=True)
ap.add_argument('--out', required=True)
a = ap.parse_args()
here = os.path.dirname(os.path.abspath(__file__))
panel = json.load(open(os.path.join(here, '..', 'inputs', 'panel.json')))
proto = json.load(open(os.path.join(L.RHO, 'protocol.json')))
info = json.load(open(os.path.join(L.RHO, 'results', 'runtime-info.json')))
P = (L.parse_z(info['P'][0]), L.parse_z(info['P'][1]))
lam = int(info['lambda'])
table, reps = L.build_base()
nat = L.Native(a.lib)
calls = []


class Spy:
    def solve(self, xr, j):
        s = nat.solve(xr, j)
        if len(s) > 1:
            calls.append({'xr': xr, 'j': j, 'solutions': s})
        return s


jobs = [('panel', p['id'], p['scalar'], p['rng_seed']) for p in panel['points']] + \
       [('archived', ii, s, proto['arms']['tau6']['rng_seed'] % ii) for ii, s in enumerate(proto['scalars'])]
out = []
for kind, pid, s, seed in jobs:
    del calls[:]
    Q = L.B.mul(s, P)
    rels = []
    # tau_dlp with the spy; R needed for validity: recompute from xr is ambiguous, so record R per call
    st = L.tau_dlp(Spy(), P, Q, lam, random.Random(seed), table, len(reps), relog=rels)
    for c in calls:
        c['in_base'] = [x1 in table and x2 in table for x1, x2 in c['solutions']]
        c['swap_pair'] = len(c['solutions']) == 2 and c['solutions'][0] == tuple(reversed(c['solutions'][1]))
    out.append({'kind': kind, 'id': pid, 'multi_calls': list(calls), 'log_ok': st['log'] == s % L.P_ORD})
res = {'kind': 'local diagnostic', 'points': out,
       'multi_calls_total': sum(len(o['multi_calls']) for o in out),
       'non_swap_multi_calls': sum(1 for o in out for c in o['multi_calls'] if not c['swap_pair']),
       'non_swap_with_two_or_more_in_base': sum(1 for o in out for c in o['multi_calls']
                                                if not c['swap_pair'] and sum(c['in_base']) >= 1)}
json.dump(res, open(a.out, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'points'}))
for o in out:
    for c in o['multi_calls']:
        if not c['swap_pair']:
            print(o['kind'], o['id'], c)

"""Local diagnostic: every (xR, j), xR in GF(2^19), j in 0..18 - how many systems
have two or more solutions, by shift, and are they all swaps (a, b), (b, a)?

    python3 multi_survey.py --lib PATH/libtau6native.so --out multi_survey.json
"""
import argparse
import json

import local_replay as L

ap = argparse.ArgumentParser()
ap.add_argument('--lib', required=True)
ap.add_argument('--out', required=True)
a = ap.parse_args()
nat = L.Native(a.lib)
by_j = {j: {'systems': 0, 'nonempty': 0, 'multi': 0, 'non_swap_multi': 0, 'max_solutions': 0} for j in range(19)}
for j in range(19):
    d = by_j[j]
    for xr in range(1 << 19):
        s = nat.solve(xr, j)
        d['systems'] += 1
        if s:
            d['nonempty'] += 1
            d['max_solutions'] = max(d['max_solutions'], len(s))
        if len(s) > 1:
            d['multi'] += 1
            if not (len(s) == 2 and s[0] == (s[1][1], s[1][0])):
                d['non_swap_multi'] += 1
json.dump({'kind': 'local diagnostic: exhaustive over xR (including 0) and every shift', 'by_shift': by_j},
          open(a.out, 'w'), indent=1)
print(json.dumps({j: (v['multi'], v['non_swap_multi'], v['max_solutions']) for j, v in by_j.items()}))

#!/usr/bin/env python3
"""Every (xR, j), xR in [0, 2^19), j in 0..18, whose variety has two or more
solutions, with the native (ascending) variety, via the v2 binding. These are
the only systems whose variety order can matter. No timing.

    python3 diagnosis/multi_list.py --lib libtau6native.so --out diagnosis/multi_systems.json
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import native_binding as nb  # noqa: E402
from s0_v2_local import run_sage_modulus  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--lib', required=True)
ap.add_argument('--out', required=True)
a = ap.parse_args()
nat = nb.Native(a.lib, 19, nb.modulus_int(run_sage_modulus()), 6)
out = []
for j in range(19):
    for xr in range(1 << 19):
        s = nat.solve(xr, j)
        if len(s) > 1:
            out.append([xr, j, s])
json.dump({'kind': 'every multi-solution shift system (native variety, ascending (u, w))',
           'count': len(out), 'systems': out}, open(a.out, 'w'), separators=(',', ':'))
print(len(out))

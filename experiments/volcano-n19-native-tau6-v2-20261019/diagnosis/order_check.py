#!/usr/bin/env python3
"""The v2 native variety order against Sage's, on every multi-solution system
(no Sage needed: Sage's orders are those recorded by the untimed Sage
diagnostic run 39329564781, sage_run_39329564781/sage_diag.json). No timing.

    python3 diagnosis/order_check.py --lib libtau6native.so --out diagnosis/order_check.json
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
d = json.load(open(os.path.join(HERE, 'sage_run_39329564781', 'sage_diag.json')))
nat = nb.Native(a.lib, 19, nb.modulus_int(run_sage_modulus()), 6)
res = {}
for name in ('s0_v1', 's0_v2', 'multi'):
    rows = d[name]['rows']
    eq = [[tuple(x) for x in r['sage']] == nat.solve(int(r['xR']), int(r['j'])) for r in rows]
    res[name] = {'systems': len(rows), 'sage_order_equals_v2_native_order': sum(eq),
                 'ascending_uw_order_agreement_recorded_by_the_diagnostic': d[name]['summary']['sage_order_eq_native_fixed_order']}
res['all_equal'] = all(v['systems'] == v['sage_order_equals_v2_native_order'] for v in res.values())
json.dump(res, open(a.out, 'w'), indent=1)
print(json.dumps(res, indent=1))
sys.exit(0 if res['all_equal'] else 1)

"""Local diagnostic (no Sage, cloud-agent VM): the candidate's control flow on the
held-out panel in pure Python + the native solve; expected counts and logs.

    python3 local_panel.py --lib PATH/libtau6native.so --out local_panel.json
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
info = json.load(open(os.path.join(L.RHO, 'results', 'runtime-info.json')))
P = (L.parse_z(info['P'][0]), L.parse_z(info['P'][1]))
lam = int(info['lambda'])
table, reps = L.build_base()
nat = L.Native(a.lib)
rows = []
for pt in panel['points']:
    Q = L.B.mul(pt['scalar'], P)
    st = L.tau_dlp(nat, P, Q, lam, random.Random(pt['rng_seed']), table, len(reps))
    st.update({'id': pt['id'], 'scalar': pt['scalar'], 'log_ok': st['log'] == pt['scalar'] % L.P_ORD})
    rows.append(st)
    print(json.dumps(st), flush=True)
json.dump({'kind': 'local diagnostic (cloud-agent VM, pure-Python driver + native solve); counts only, '
                   'not timing evidence', 'points': rows,
           'all_logs_ok': all(r['log_ok'] and r['recovered'] for r in rows)}, open(a.out, 'w'), indent=1)

#!/usr/bin/env python3
"""Validator report for the lead_sweep runs (fresh/ and ext/): runner verdict (claimed) vs analyze.py recompute from raw arm JSONs."""
import json, glob, hashlib, os, sys, subprocess
heads, raw = [], []
for vf in sorted(glob.glob('fresh/*/*/verdict.json') + glob.glob('ext/*/*/verdict.json')):
    v = json.load(open(vf)); d = os.path.dirname(vf); assert v['verdict'] == 'PASS'
    for c in v['cells']:
        base = f"{d}/cells/{c['id']}/baseline.json"; raw.append(base)
        for m in ('2', '3'):
            arm = f"{d}/cells/{c['id']}/lead-m{m}.json"; raw.append(arm)
            out = json.loads(subprocess.run(['python3', 'analyze.py', base, arm], capture_output=True, text=True, check=True).stdout)
            tag = f"{vf.split('/')[0]} {c['id']} m{m}"
            b = c['by_m'][m]
            heads.append({'name': tag + ' geomean S ratio', 'claimed': b['speedup_geomean'], 'recomputed': out['S'][0], 'rel_tol': 1e-9})
            heads.append({'name': tag + ' CI lo', 'claimed': b['speedup_ci'][0], 'recomputed': out['S'][1], 'rel_tol': 0.01})
            heads.append({'name': tag + ' CI hi', 'claimed': b['speedup_ci'][1], 'recomputed': out['S'][2], 'rel_tol': 0.01})
        raw.append(f"{d}/cells/{c['id']}/baseline.json")
raw += sorted(glob.glob('fresh/*/*/verdict.json') + glob.glob('ext/*/*/verdict.json'))
raw = sorted(set(raw))
json.dump({'schema': 'validator-report/lead-sweep-recompute/v1', 'status': 'pass',
           'what': 'runner verdicts (baseline/lead priced-S ratios, paired by planted target, geomean and 95% percentile bootstrap, 10,000 resamples, seed 20261119) recomputed from the raw ca-ic arm JSONs by analyze.py; every row verified [d]G = Q',
           'raw_data': [{'path': p, 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()} for p in raw], 'headline': heads},
          open('validator-report.json', 'w'), indent=1)
print(len(heads), max(abs(h['claimed'] - h['recomputed']) / h['claimed'] for h in heads))

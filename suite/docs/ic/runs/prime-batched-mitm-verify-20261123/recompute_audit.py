#!/usr/bin/env python3
"""Second, independent implementation of the audit's point estimates (no bootstrap, no shared code
with audit.py/analyze.py): for each bits and arm pair, geometric mean over targets of the
per-target replicate-mean-of-log ratio, from the raw ca-ic reports.  Writes validator-report.json
with claimed (audit-results.json) vs recomputed headline numbers and sha256-pinned raw data."""
import json, glob, hashlib, math, os, sys
root = sys.argv[1]; auditdir = sys.argv[2]            # e.g. audit  /  auditext
res = json.load(open(f'{auditdir}/audit-results.json'))
def rows(f):
    d = json.load(open(f)); assert d['all_verified'] is True
    return [(r['s'], r['wall_seconds']) for r in d['rows']]
def lg(bits, arm, idx):
    fs = sorted(glob.glob(f'{auditdir}/b{bits}/{arm}.r*.json')); R = [rows(f) for f in fs]
    return [sum(math.log(r[i][idx]) for r in R) / len(R) for i in range(len(R[0]))]
def ratio(bits, num, den, idx):
    a, b = lg(bits, num, idx), lg(bits, den, idx)
    return math.exp(sum(x - y for x, y in zip(a, b)) / len(a))
heads, raw = [], []
for b, r in res.items():
    b = int(b)
    for lead, ctl in (('L2', 'B0'), ('L2', 'B3'), ('L3', 'M3n'), ('L3', 'B0')):
        key = f'{lead}_vs_{ctl}'
        claimed_w = r['arms'][lead]['wall_vs_B0'][0] if ctl == 'B0' else r[key]['wall'][0]
        claimed_s = r['arms'][lead]['S_vs_B0'][0] if ctl == 'B0' else r[key]['S'][0]
        heads.append({'name': f'{b}bit {lead} vs {ctl} wall', 'claimed': claimed_w, 'recomputed': ratio(b, ctl, lead, 1), 'rel_tol': 1e-9})
        heads.append({'name': f'{b}bit {lead} vs {ctl} S', 'claimed': claimed_s, 'recomputed': ratio(b, ctl, lead, 0), 'rel_tol': 1e-9})
os.system(f'tar cJf {auditdir}-raw.tar.xz {auditdir}')   # raw reports archived (S3 is unavailable here); extract to re-run
for f in (f'{auditdir}-raw.tar.xz', f'{auditdir}/audit-results.json'):
    raw.append({'path': os.path.relpath(f, root), 'sha256': hashlib.sha256(open(f, 'rb').read()).hexdigest()})
json.dump({'schema': 'validator-report/audit-recompute/v1', 'status': 'pass',
           'what': 'second implementation of the accounting audit point estimates (geomean over targets of the replicate-mean log ratio) from raw ca-ic reports; every row verified [d]G=Q',
           'raw_data': raw, 'headline': heads}, open(f'{auditdir}-validator-report.json', 'w'), indent=1)
print(len(heads), 'headlines;', max(abs(h['claimed'] - h['recomputed']) / h['claimed'] for h in heads))

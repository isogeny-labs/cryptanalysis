#!/usr/bin/env python3
"""Independent paired analysis of ca-ic bench reports (does not use lead_sweep.py).
usage: analyze.py BASE.json ARM.json [ARM.json ...]   (all on the same instance/seeds)
Pairs rows by (planted logarithm, repeat index); prints geomean(base/arm) with 95% percentile
bootstrap (10,000 resamples, seed 20261119) for: S (priced), wall-S (total wall / ns_per_add / sqrt r),
and per-phase GAE (setup+decomposition-run).  Every row must be verified."""
import json, sys, math, random
def load(p):
    d = json.load(open(p)); rows = d['rows']; ns = d['calibration']['ns_per_add']
    out = {}
    for i, r in enumerate(rows):
        assert r['verified'] and r['recovered'] is not None, (p, i)
        sw = r['wall_seconds'] * 1e9 / ns / math.sqrt(r['r'])
        dec = r['decomposition']
        out[(r['recovered'], i)] = dict(s=r['s'], sw=sw, gae=r['total_gae'], r=r['r'], ns=ns,
              trials=dec.get('targets_tried'), rel=dec.get('relations_found'),
              setup=(dec.get('setup') or {}).get('gae', 0.0), run=(dec.get('cost') or {}).get('gae', 0.0),
              setup_wall=(dec.get('setup') or {}).get('wall_ns', 0), rho=r['rho_s'], inst=r['instance'])
    return out, d['all_verified']
def ci(logs, seed=20261119, B=10000):
    rng = random.Random(seed); n = len(logs); ms = sorted(sum(rng.choice(logs) for _ in range(n)) / n for _ in range(B))
    return math.exp(ms[int(0.025 * B)]), math.exp(ms[int(0.975 * B) - 1])
def gm(x): return math.exp(sum(math.log(v) for v in x) / len(x))
def main(a):
    base, bv = load(a[0]); res = []
    for p in a[1:]:
        arm, av = load(p); keys = sorted(set(base) & set(arm))
        assert len(keys) == len(base) == len(arm), 'pairing broken'
        row = dict(arm=p.split('/')[-1], n=len(keys), verified=bv and av,
                   base_S=sum(base[k]['s'] for k in keys) / len(keys), arm_S=sum(arm[k]['s'] for k in keys) / len(keys),
                   same_trials=all(base[k]['trials'] == arm[k]['trials'] and base[k]['rel'] == arm[k]['rel'] for k in keys),
                   rho=sum(base[k]['rho'] for k in keys) / len(keys))
        for name, f in (('S', 's'), ('wallS', 'sw'), ('gae', 'gae')):
            l = [math.log(base[k][f] / arm[k][f]) for k in keys]
            row[name] = (math.exp(sum(l) / len(l)),) + ci(l)
        row['S_over_rho'] = row['arm_S'] / row['rho']
        res.append(row)
    return res
if __name__ == '__main__':
    for r in main(sys.argv[1:]):
        print(json.dumps(r))

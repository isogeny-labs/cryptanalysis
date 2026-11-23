#!/usr/bin/env python3
"""Accounting audit runner + analysis (protocol amendment 1).  run: audit.py run OUTDIR; analyse: audit.py an OUTDIR"""
import json, subprocess, sys, os, math, random, glob
CA = '/home/user/wt/mitm-batched-verify/suite/target/release/ca-ic'
INST = {16: (40, 887597270407), 18: (63, 887597270407), 20: (100, 69066127048), 22: (160, 69066127048), 24: (256, 509897497596)}
ARMS = {  # name: (oracle string, rho_runs)
 'B0':   ('mitm', 8), 'B1': ('mitm:negation_folded=1', 0), 'B2': ('mitm:native_setup_pricing=1', 0),
 'B3':   ('mitm:negation_folded=1,native_setup_pricing=1', 0),
 'L2':   ('mitm-prime-batched:m=2', 0), 'L2c': ('mitm-prime-batched:m=2,native_setup_pricing=0', 0),
 'M3':   ('mitm:m=3', 0), 'M3n': ('mitm:m=3,native_setup_pricing=1', 0),
 'L3':   ('mitm-prime-batched:m=3', 0), 'L3c': ('mitm-prime-batched:m=3,native_setup_pricing=0,native_probe_pricing=0', 0)}
def run(out, R=5, reps=24, bits_list=(16, 18, 20, 22, 24)):
    names = list(ARMS)
    for b in bits_list:
        size, seed = INST[b]
        for rep in range(R):
            order = names[rep % len(names):] + names[:rep % len(names)]
            for a in order:
                f = f'{out}/b{b}/{a}.r{rep}.json'; os.makedirs(os.path.dirname(f), exist_ok=True)
                o, rho = ARMS[a]
                cmd = ['taskset', '-c', '3', CA, 'bench', '--bits', str(b), '--factor-base', f'prime-abscissa:size={size}', '--oracle', o,
                       '--repeats', str(reps), '--seed', str(seed), '--max-trials', '8000000', '--max-cofactor', '8',
                       '--solver-budget-seconds', '600', '--rho-runs', str(rho), '--json', '--out', f]
                r = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, 'RAYON_NUM_THREADS': '1'})
                if r.returncode: print('FAIL', a, b, rep, r.stderr[-300:])
        print('bits', b, 'load', open('/proc/loadavg').read().strip(), flush=True)
def ci(l, seed=20261119, B=10000):
    rng = random.Random(seed); n = len(l); ms = sorted(sum(rng.choice(l) for _ in range(n)) / n for _ in range(B))
    return math.exp(ms[int(.025 * B)]), math.exp(ms[int(.975 * B) - 1])
def load(f):
    d = json.load(open(f)); assert d['all_verified']
    return {i: dict(s=r['s'], w=r['wall_seconds'], key=r['recovered'], tr=r['decomposition']['targets_tried'], rel=r['decomposition']['relations_found'],
                    ns=d['calibration']['ns_per_add'], r=r['r'], rho=r['rho_s'], setup_w=(r['decomposition'].get('setup') or {}).get('wall_ns', 0),
                    setup_g=(r['decomposition'].get('setup') or {}).get('gae', 0), inst=r['instance']) for i, r in enumerate(d['rows'])}
def an(out):
    res = {}
    for bd in sorted(glob.glob(out + '/b*'), key=lambda x: int(x.split('/b')[-1])):
        b = int(bd.split('/b')[-1]); data = {}
        for a in ARMS:
            fs = sorted(glob.glob(f'{bd}/{a}.r*.json'))
            if fs: data[a] = [load(f) for f in fs]
        def agg(a, k):  # per-target mean over replicates
            reps = data[a]; return [sum(r[i][k] for r in reps) / len(reps) for i in range(len(reps[0]))]
        def lgm(a, k):  # per-target mean of log over replicates
            reps = data[a]; return [sum(math.log(r[i][k]) for r in reps) / len(reps) for i in range(len(reps[0]))]
        rho = sum(r['rho'] for r in data['B0'][0].values()) / len(data['B0'][0])
        row = {'bits': b, 'instance': data['B0'][0][0]['inst'], 'rho_S': rho, 'reps': len(data['B0']), 'targets': len(data['B0'][0]), 'arms': {}}
        for a in data:
            ls = lgm(a, 's'); lw = lgm(a, 'w'); l0s = lgm('B0', 's'); l0w = lgm('B0', 'w')
            rs = [x - y for x, y in zip(l0s, ls)]; rw = [x - y for x, y in zip(l0w, lw)]
            same = all(data['B0'][0][i]['tr'] == data[a][0][i]['tr'] and data['B0'][0][i]['rel'] == data[a][0][i]['rel'] for i in data['B0'][0])
            row['arms'][a] = dict(S_mean=sum(agg(a, 's')) / row['targets'], wall_ms=1e3 * sum(agg(a, 'w')) / row['targets'],
                setup_wall_ms=1e-6 * sum(agg(a, 'setup_w')) / row['targets'],
                S_vs_B0=[math.exp(sum(rs) / len(rs)), *ci(rs)], wall_vs_B0=[math.exp(sum(rw) / len(rw)), *ci(rw)], same_trials_rel_as_B0=same,
                S_over_rho=sum(agg(a, 's')) / row['targets'] / rho)
        # vs same-priced scalar controls (wall)
        for lead, ctl in (('L2', 'B3'), ('L2', 'B2'), ('L2', 'B1'), ('L3', 'M3n'), ('L3', 'M3')):
            lw = [x - y for x, y in zip(lgm(ctl, 'w'), lgm(lead, 'w'))]; ls = [x - y for x, y in zip(lgm(ctl, 's'), lgm(lead, 's'))]
            row[f'{lead}_vs_{ctl}'] = dict(wall=[math.exp(sum(lw) / len(lw)), *ci(lw)], S=[math.exp(sum(ls) / len(ls)), *ci(ls)])
        res[b] = row
    json.dump(res, open(out + '/audit-results.json', 'w'), indent=1); return res
if __name__ == '__main__':
    if sys.argv[1] == 'run': run(sys.argv[2], *(int(x) for x in sys.argv[3:5]))
    else:
        res = an(sys.argv[2])
        f = lambda v: '%.2f [%.2f,%.2f]' % tuple(v)
        for b, r in res.items():
            print(f"== {b} bits  {r['instance']}  rho_S {r['rho_S']:.2f}  targets {r['targets']} reps {r['reps']}")
            for a, x in r['arms'].items():
                print(f"  {a:4s} S {x['S_mean']:7.2f} (S/rho {x['S_over_rho']:5.1f}) wall {x['wall_ms']:7.2f} ms setup {x['setup_wall_ms']:6.2f} ms | S vs B0 {f(x['S_vs_B0'])} | wall vs B0 {f(x['wall_vs_B0'])} | same {x['same_trials_rel_as_B0']}")
            for k in r:
                if '_vs_' in k: print(f"  {k}: wall {f(r[k]['wall'])}  S {f(r[k]['S'])}")

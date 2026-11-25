#!/usr/bin/env python3
"""Tune (on seeds 101,102) then evaluate (seeds 1..6) the pair-table batch IC. Two worker processes."""
import sys, os, csv, json, math, resource, multiprocessing as mp
sys.path.insert(0, os.path.dirname(__file__))
from pt_ic import run
ICDIR = '/tmp/claude-0/scr/ic'
KS = [1, 4, 16, 64, 256, 1024, 4096]
OUT = '/tmp/claude-0/scr/pt'
os.makedirs(OUT, exist_ok=True)
def path(B, s): return f'{ICDIR}/generic_b{B}_k4096_s{s}.json'
RS = {20: 6e5, 24: 1.1e7, 28: 1.9e8}
def nstar(B, K, start):
    r = RS[B]; smul = 1.5*math.log2(r); best = None
    for N in range(8, 3000):
        h = 2*N*N/r * 0.9
        tot = N*(2*N+1) + 1.5*N*math.log(N+2)/ (2*N*N/r) + K*(1/h + (smul*(2 if start == 'full' else 1)+1)*(1 if start=='full' else 0.2))
        if best is None or tot < best[0]: best = (tot, N)
    return best[1]
def job(a):
    kind, B, s, K, N, f, start, rep = a
    try:
        d = run(path(B, s), B, s, K, N, f, start, rep)
    except Exception as e:
        d = dict(B=B, seed=s, K=K, N=N, fstop=f, start=start, rep=rep, ops=float('nan'), status='ERR '+repr(e)[:80])
    d['kind'] = kind
    return d
def writecsv(rows, fn):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with open(fn, 'w', newline='') as fh:
        w = csv.DictWriter(fh, keys); w.writeheader(); w.writerows(rows)
if __name__ == '__main__':
    resource.setrlimit(resource.RLIMIT_AS, (6 << 30, 6 << 30))
    phase = sys.argv[1]
    pool = mp.Pool(2)
    if phase == 'tune':
        jobs = []
        for B in (20, 24, 28):
            for K in (1, 16, 256, 4096):
                for start in ('full', 'cheap'):
                    n0 = nstar(B, K, start)
                    for m in (0.35, 0.5, 0.7, 1.0, 1.4):
                        N = max(8, int(n0*m))
                        for f in (0.8, 0.95):
                            for s in (101, 102):
                                for rep in (0,):
                                    jobs.append(('tune', B, s, K, N, f, start, rep))
        rows = pool.map(job, jobs, chunksize=4)
        writecsv(rows, f'{OUT}/tune.csv')
        # choose
        from collections import defaultdict
        agg = defaultdict(list)
        for r in rows:
            if r['status'] == 'complete': agg[(r['B'], r['K'], r['start'], r['N'], r['fstop'])].append(r['ops_per_target'])
        best = {}
        for (B, K, st, N, f), v in agg.items():
            m = sum(v)/len(v)
            if (B, K, st) not in best or m < best[(B, K, st)][0]: best[(B, K, st)] = (m, N, f)
        json.dump({f'{B}|{K}|{st}': [m, N, f] for (B, K, st), (m, N, f) in best.items()}, open(f'{OUT}/chosen.json', 'w'), indent=1)
        print('tuned', len(rows))
    else:
        ch0 = json.load(open(f'{OUT}/chosen.json')); ch = {}
        for B in (20, 24, 28):
            for st in ('full', 'cheap'):
                pts = [(math.log(K), ch0[f'{B}|{K}|{st}'][1], ch0[f'{B}|{K}|{st}'][2]) for K in (1, 16, 256, 4096)]
                for K in KS:
                    x = math.log(K)
                    for (x0, n0, f0), (x1, n1, f1) in zip(pts, pts[1:]):
                        if x0 <= x <= x1 + 1e-9:
                            t = (x-x0)/(x1-x0); ch[f'{B}|{K}|{st}'] = [0, int(round(math.exp((1-t)*math.log(n0)+t*math.log(n1)))), f0 if t < .5 else f1]; break
        jobs = []
        for B in (20, 24, 28):
            for s in range(1, 7):
                for K in KS:
                    for start in ('full', 'cheap'):
                        m, N, f = ch[f'{B}|{K}|{start}']
                        for rep in range(2 if K <= 256 else 1):
                            jobs.append(('eval', B, s, K, N, f, start, rep))
                        if start == 'full' and K in (64, 4096):   # sensitivity: symmetry-exploiting table charge
                            jobs.append(('eval_sym', B, s, K, N, f, start, 0))
        rows = pool.map(job, jobs, chunksize=2)
        writecsv(rows, f'{OUT}/eval.csv')
        print('evaluated', len(rows), 'fail', sum(r['status'] != 'complete' for r in rows))

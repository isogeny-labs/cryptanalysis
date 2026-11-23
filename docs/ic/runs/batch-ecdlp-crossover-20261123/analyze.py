#!/usr/bin/env python3
import csv, math, random, json, sys, collections
D = '/home/user/workspace/docs/notes/batch-ecdlp-crossover-20261123/'
PT = '/tmp/claude-0/scr/pt/eval.csv'
cells = list(csv.DictReader(open(D+'rho_lp_cells.csv')))
ev = [r for r in csv.DictReader(open(PT)) if r['kind'] == 'eval']
rng = random.Random(20261123)
# executed rho per (B,seed,K,fold,start) and IC-LP per (B,seed,K)
rho = {}; lp = {}
for c in cells:
    k = (int(c['B']), int(c['seed']), int(c['K']))
    lp[k] = float(c['ic_ops'])
    rho[k+(int(c['fold']), c['start'])] = float(c['rho_mean'])
def ptmean(B, s, K, start, table='tool'):
    xs = []
    for r in ev:
        if int(r['B']) == B and int(r['seed']) == s and int(r['K']) == K and r['start'] == start:
            if r['status'] != 'complete': return None
            o = float(r['ops'])
            N = int(r['N'])
            if table == 'batched': o = o - float(r['op_table']) + N*(N+1)
            if table == 'priced':   # mixed unit: table at ic bench's measured native pricing (gae/(N(N+1)) = 0.615 at N=100, 0.281 at N=256; power law between/beyond)
                rho_n = 0.615*(N/100.0)**(math.log(0.281/0.615)/math.log(2.56))
                o = o - float(r['op_table']) + N*(N+1)*rho_n
            xs.append(o)
    return sum(xs)/len(xs) if xs else None
def gm(v): return math.exp(sum(math.log(x) for x in v)/len(v))
def boot(v, n=10000):
    ms = []
    for _ in range(n):
        s = [v[rng.randrange(len(v))] for _ in v]; ms.append(gm(s))
    ms.sort(); return ms[int(.025*n)], ms[int(.975*n)]
def cross(Ks, ratios):
    # smallest K where ratio (IC/rho) falls below 1, log-K interpolation; None if never
    for i in range(len(Ks)):
        if ratios[i] < 1:
            if i == 0: return float(Ks[0])
            x0, x1 = math.log(Ks[i-1]), math.log(Ks[i]); y0, y1 = ratios[i-1], ratios[i]
            return math.exp(x0 + (1-y0)*(x1-x0)/(y1-y0))
    return None
Ks = [1, 4, 16, 64, 256, 1024, 4096]
out = []
arms = [('IC-LP', lambda B, s, K, st: lp.get((B, s, K))),
        ('IC-PT tool-table', lambda B, s, K, st: ptmean(B, s, K, st, 'tool')),
        ('IC-PT batched-table', lambda B, s, K, st: ptmean(B, s, K, st, 'batched')),
        ('IC-PT priced-table (mixed unit)', lambda B, s, K, st: ptmean(B, s, K, st, 'priced'))]
res = {}
w = open(D+'RESULTS_TABLES.md', 'w')
for st, label in (('full', 'folded batch rho, tool seeding (full)'), ('cheap', 'best-seeded folded batch rho (cheap)')):
    w.write(f'\n## IC / {label}: geometric mean over 6 curves of (IC total / executed rho total), 95% bootstrap CI\n\n')
    for B in (20, 24, 28):
        w.write(f'\n### B = {B}\n\n| arm | ' + ' | '.join(f'K={K}' for K in Ks) + ' | per-curve crossing K (curves 1..6) | median crossing |\n|--|' + '--|'*(len(Ks)+2) + '\n')
        for name, f in arms:
            if name == 'IC-LP' and False: pass
            row = []; per = {s: [] for s in range(1, 7)}; ok = True
            for K in Ks:
                rr = []
                for s in range(1, 7):
                    a = f(B, s, K, st if name != 'IC-LP' else st)
                    b = rho.get((B, s, K, 1, st))
                    if a is None or b is None: ok = False; break
                    rr.append(a/b); per[s].append(a/b)
                if not ok: break
                lo, hi = boot(rr)
                row.append(f'{gm(rr):.2f} [{lo:.2f},{hi:.2f}]')
                res[(st, B, name, K)] = (gm(rr), lo, hi)
            if not ok: w.write(f'| {name} | (missing) |\n'); continue
            cr = [cross(Ks, per[s]) for s in range(1, 7)]
            crs = ', '.join('none' if c is None else f'{c:.0f}' for c in cr)
            cv = sorted(c for c in cr if c is not None)
            med = 'none' if len(cv) < 3 else f'{cv[len(cv)//2]:.0f} ({len(cv)}/6 cross)'
            w.write(f'| {name} | ' + ' | '.join(row) + f' | {crs} | {med} |\n')
# up-front and per-target cost: fit total = A + K*D per arm on each curve? report A (K=1 ops minus descent) via PT components
w.write('\n## IC-PT components (mean over curves; ops in the abstract unit), full seeding, chosen N\n\n| B | K | N (median) | table | jumps | rel steps+seed | desc steps | desc seed | total/K |\n|--|--|--|--|--|--|--|--|--|\n')
for B in (20, 24, 28):
    for K in Ks:
        rs = [r for r in ev if int(r['B']) == B and int(r['K']) == K and r['start'] == 'full']
        if not rs: continue
        m = lambda k: sum(float(r[k]) for r in rs)/len(rs)
        Ns = sorted(int(r['N']) for r in rs)
        w.write(f"| {B} | {K} | {Ns[len(Ns)//2]} | {m('op_table'):.0f} | {m('op_jumps'):.0f} | {m('op_rel_steps')+m('op_rel_seed'):.0f} | {m('op_desc_steps'):.0f} | {m('op_desc_seed'):.0f} | {m('ops')/K:.1f} |\n")
w.close()
print(open(D+'RESULTS_TABLES.md').read())

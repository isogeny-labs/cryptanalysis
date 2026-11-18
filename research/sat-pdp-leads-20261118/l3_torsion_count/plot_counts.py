#!/usr/bin/env python3
"""Graph for the L3 count: observed vs estimated relations per factor base."""
import json, collections
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
t = [json.loads(l) for l in open('results.jsonl')]
c = [json.loads(l) for l in open('control.jsonl')][:-1]
def agg(rows, div):
    g = collections.defaultdict(lambda: [0, 0.0, 0])
    for r in rows:
        k = (r['n'], r['l']); g[k][0] += r['xsets']; g[k][1] += r['est_ordered'] / div; g[k][2] += 1
    return g
gt, gc = agg(t, 12), agg(c, 6)
cells = sorted(gt); x = range(len(cells))
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.semilogy(x, [gt[k][1] / gt[k][2] for k in cells], 'o--', color='#1f77b4', mfc='none', label='T0 target: estimate N³/(12·2ⁿ)')
ax.semilogy(x, [max(gt[k][0] / gt[k][2], 1e-3) for k in cells], 'o', color='#1f77b4', label='T0 target: observed (0 drawn at 1e-3)')
ax.semilogy(x, [gc[k][1] / gc[k][2] for k in cells], 's--', color='#d62728', mfc='none', label='random-target control: estimate N³/(6·2ⁿ)')
ax.semilogy(x, [max(gc[k][0] / gc[k][2], 1e-3) for k in cells], 's', color='#d62728', label='random-target control: observed')
ax.semilogy(x, [2 ** l for n, l in cells], 'k-', lw=1, label='2^l ≈ relations needed per factor base')
ax.set_xticks(list(x)); ax.set_xticklabels([f"{n},{l}" for n, l in cells], rotation=45)
ax.set_xlabel('(n, l)'); ax.set_ylabel('x-set relations per factor base (mean, 40 curves)')
ax.set_title('L3: exact counts of P1+P2+P3 = T0 over V = span(1, z, …, z^(l-1))')
ax.legend(fontsize=7, loc='center right'); fig.tight_layout()
fig.savefig('l3_counts.svg'); fig.savefig('l3_counts.png', dpi=150)

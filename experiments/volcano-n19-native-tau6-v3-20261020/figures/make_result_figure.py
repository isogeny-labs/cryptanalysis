"""Run 39387473809 result figure (valid; verdict improvement).

    python3 make_result_figure.py   -> result.svg, result.png (next to this script)
Data: ../run_github_39387473809/timed/panel/result.json
The first run's invalid outcome is kept in invalid_run1.* (make_invalid_run1_figure.py).
"""
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
r = json.load(open(os.path.join(HERE, '..', 'run_github_39387473809', 'timed', 'panel', 'result.json')))
st = r['statistics']
pairs = st['per_pair']
pts = sorted({p['point'] for p in pairs})
prim = st['primary_cold_cpu_B_over_N']
fig, (a, b) = plt.subplots(1, 2, figsize=(10.4, 4.2), gridspec_kw={'width_ratios': [1.7, 1]})
for i, pt in enumerate(pts):
    for k, p in enumerate([q for q in pairs if q['point'] == pt]):
        a.plot(i + (k - 1) * 0.18, p['ratio'], 'o' if p['first'] == 'B' else 's',
               color='#2b6cb0' if p['first'] == 'B' else '#dd8a2a', ms=4)
a.axhspan(prim['ci95'][0], prim['ci95'][1], color='#2b6cb0', alpha=0.13)
a.axhline(prim['estimate'], color='#2b6cb0', lw=1)
a.plot([], [], 'o', color='#2b6cb0', label='B first')
a.plot([], [], 's', color='#dd8a2a', label='N first')
a.legend(frameon=False, fontsize=8, loc='lower left', ncol=2)
a.set_xticks(range(len(pts)))
a.set_xticklabels(pts, rotation=60, fontsize=7)
a.set_ylabel('cold CPU, B / N, per pair')
a.set_title('R = %.1f [%.1f, %.1f] over %d pairs; verdict %s' % (
    prim['estimate'], prim['ci95'][0], prim['ci95'][1], prim['n_pairs'], r['verdict']), fontsize=9, loc='left')
a.spines[['top', 'right']].set_visible(False)
S = st['S']
rho = st['rho']['S_cold']
names = ['B', 'NX', 'N', 'Naa']
setup = [S[k]['setup'] for k in names] + [0]
online = [S[k]['online'] for k in names] + [rho]
labels = names + ['rho']
for i in range(len(labels)):
    b.barh(i, setup[i], color='#8a8f98', label='setup' if i == 0 else None)
    b.barh(i, online[i], left=setup[i], color='#2b6cb0', label='online (rho: whole run)' if i == 0 else None)
    b.text(setup[i] + online[i] * 1.15, i, '%.4g' % (setup[i] + online[i]), va='center', fontsize=7)
b.set_xscale('log'); b.set_xlim(0.1, 3e4)
b.set_yticks(range(len(labels))); b.set_yticklabels(labels, fontsize=8); b.invert_yaxis()
b.set_xlabel('S, cold (this run\'s rho group operation; log)', fontsize=8)
b.legend(frameon=False, fontsize=7, loc='lower right')
b.set_title('A/A %.4f [%.4f, %.4f]; planted %.1f [%.1f, %.1f]' % (
    st['aa_cold_cpu_N_over_Naa']['estimate'], *st['aa_cold_cpu_N_over_Naa']['ci95'],
    st['planted_cold_cpu_NX_over_N']['estimate'], *st['planted_cold_cpu_NX_over_N']['ci95']), fontsize=8, loc='left')
b.spines[['top', 'right']].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(HERE, 'result.svg'), bbox_inches='tight')
fig.savefig(os.path.join(HERE, 'result.png'), dpi=160, bbox_inches='tight')

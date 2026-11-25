"""Figure for run_github_39376405326 (invalid): gate and row outcomes, from its archived receipt.

    python3 figures/make_result_figure.py        (reads run_github_39376405326/panel, writes figures/result.{svg,png})
"""
import collections
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(HERE, 'run_github_39376405326', 'panel')
res = json.load(open(os.path.join(P, 'result.json')))
runs = [json.loads(l) for l in open(os.path.join(P, 'runs.jsonl'))]

def kind(row):
    a = row.split('-', 1)[-1] if row[0] == 'p' else row
    return {'S0-selftest': 'S0', 'O1-archived': 'O1'}.get(row, a)

ok, bad = collections.Counter(), collections.Counter()
for r in runs:
    k = kind(r['row'])
    (ok if r['exit'] == 0 else bad)[k] += 1
order = ['S0', 'O1', 'rho', 'B', 'N', 'Naa', 'NX']
gates = res['gates']
npass = sum(1 for g in gates.values() if g['pass'])

fig, ax = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={'width_ratios': [3, 2]})
a = ax[0]
a.bar(order, [ok[k] for k in order], color='#3b7dd8', label='exit 0')
a.bar(order, [bad[k] for k in order], bottom=[ok[k] for k in order], color='#d8553b', label='exit 1 (TypeError)')
for i, k in enumerate(order):
    a.text(i, ok[k] + bad[k] + 0.3, str(ok[k] + bad[k]), ha='center', fontsize=9)
a.set_ylabel('scheduled rows'); a.set_title('Rows by arm: all 64 timed IC rows crashed')
a.set_ylim(0, 22); a.legend(frameon=False, loc='upper left'); a.spines[['top', 'right']].set_visible(False)
b = ax[1]
b.bar(['pass', 'fail'], [npass, len(gates) - npass], color=['#3b7dd8', '#d8553b'])
for i, v in enumerate([npass, len(gates) - npass]):
    b.text(i, v + 1, str(v), ha='center', fontsize=9)
b.set_ylim(0, 95); b.set_title('Gates (118): S0 and field check pass'); b.spines[['top', 'right']].set_visible(False)
fig.suptitle('Run 39376405326, protocol v2: verdict invalid; no ratio exists', fontsize=11)
fig.tight_layout()
os.makedirs(os.path.join(HERE, 'figures'), exist_ok=True)
for ext in ('svg', 'png'):
    fig.savefig(os.path.join(HERE, 'figures', 'result.' + ext), dpi=150)

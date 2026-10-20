"""Run 39384735073 outcome figure (invalid; no timing exists).

    python3 make_result_figure.py   -> result.svg, result.png (next to this script)
Data: ../run_github_39384735073/run-record.json
"""
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
rec = json.load(open(os.path.join(HERE, '..', 'run_github_39384735073', 'run-record.json')))
steps = [('1 set up job', 'ok'), ('2 checkout', 'ok'), ('3 freeze runner and source identity', 'fail'),
         ('4 planted corruptions', 'skip'), ('5 build native solve', 'skip'), ('6 pull Sage image', 'skip'),
         ('7 digest_repro.sage diagnosis', 'skip'), ('8 smoke part', 'skip'), ('9 smoke gate', 'skip'),
         ('10 preserve receipt (always)', 'ok'), ('timed job (20 points, 60 B/N pairs)', 'skip')]
col = {'ok': '#3f9142', 'fail': '#c0392b', 'skip': '#9aa5b1'}
fig, ax = plt.subplots(figsize=(7.2, 3.8))
for i, (name, st) in enumerate(steps):
    ax.barh(len(steps) - 1 - i, 1, color=col[st])
    ax.text(1.03, len(steps) - 1 - i, name + {'ok': ' - ran', 'fail': ' - KeyError: N19_RD', 'skip': ' - skipped'}[st],
            va='center', fontsize=8)
ax.set_xlim(0, 3.2); ax.axis('off')
ax.set_title('Run 39384735073: sage-smoke failed in step 3 after 2 s; no experiment code ran; verdict invalid',
             fontsize=9, loc='left')
fig.savefig(os.path.join(HERE, 'result.svg'), bbox_inches='tight')
fig.savefig(os.path.join(HERE, 'result.png'), dpi=160, bbox_inches='tight')

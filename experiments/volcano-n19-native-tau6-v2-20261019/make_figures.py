"""Figures for volcano-n19-native-tau6-v2-20261019 (matplotlib), protocol v2.

    python3 make_figures.py design          figures/{baseline_phases,design,power,s0_diagnosis}.{svg,png} (before any run)
    python3 make_figures.py result RECEIPT  RECEIPT/figures/result.{svg,png} (from result.json)
"""
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ARCH = os.path.join(HERE, '..', 'volcano-ic', 'rho-arm-20261014', 'results', 'arms.jsonl')
INK, MUTED, A1, A2, A3 = '#1f2933', '#7b8794', '#2f6fbd', '#d9822b', '#3f9142'


def save(fig, base):
    fig.savefig(base + '.svg', bbox_inches='tight')
    fig.savefig(base + '.png', dpi=160, bbox_inches='tight')
    plt.close(fig)


def baseline_phases(out):
    rows = [json.loads(l) for l in open(ARCH)]
    t = sorted((r for r in rows if r['arm'] == 'tau6'), key=lambda r: r['instance'])
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    xs = range(len(t))
    gb = [r['gb_cpu_s'] for r in t]
    rest = [r['relation_cpu_s'] - r['gb_cpu_s'] for r in t]
    la = [r['linalg_cpu_s'] for r in t]
    ax.bar(xs, gb, color=A1, label='per-shift Groebner solve (gb_cpu_s)')
    ax.bar(xs, rest, bottom=gb, color=A2, label='rest of relation search')
    ax.bar(xs, la, bottom=[g + r for g, r in zip(gb, rest)], color=A3, label='linear algebra')
    ax.set_xticks(list(xs))
    ax.set_xticklabels(['%d' % r['scalar'] for r in t], rotation=45, fontsize=7)
    ax.set_xlabel('archived planted scalar (run 38520305068)')
    ax.set_ylabel('CPU s per complete ECDLP')
    tot = sum(r['total_cpu_s'] for r in t)
    ax.set_title('Baseline tau6 cost by phase: Groebner %.1f%% of %.1f s over 10 ECDLPs' %
                 (100 * sum(gb) / tot, tot), fontsize=9)
    ax.legend(fontsize=7, frameon=False, loc='upper left')
    ax.spines[['top', 'right']].set_visible(False)
    save(fig, os.path.join(out, 'baseline_phases'))


def design(out):
    fig, ax = plt.subplots(figsize=(8.8, 3.9))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis('off')

    def box(x, y, w, h, text, c):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.05', fc='white', ec=c, lw=1.4))
        ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=7.2, color=INK)

    box(0.1, 3.6, 2.2, 1.0, 'tauDlp\n(tau.sage, unchanged):\nrng, R = aP + bQ, shifts', INK)
    box(2.9, 3.6, 3.0, 1.0, 'tauRelation per shift j\nB: Sage system + GB + variety\nN: native variety (Rust)', A1)
    box(6.5, 3.6, 3.3, 1.0, 'same checks: x in V\' base,\n+-P1 +- tau^j P2 == R\n-> relation (col, sign, e)', INK)
    ax.annotate('', xy=(2.9, 4.1), xytext=(2.3, 4.1), arrowprops=dict(arrowstyle='->', color=MUTED))
    ax.annotate('', xy=(6.5, 4.1), xytext=(5.9, 4.1), arrowprops=dict(arrowstyle='->', color=MUTED))
    box(0.1, 1.9, 9.7, 1.1, 'per held-out point (16 new scalars): one fresh pinned Sage process per arm, shuffled order\n'
        'B baseline | N candidate | Naa A/A\n'
        'NX planted (N + Sage solve redone, compared, discarded) | rho matched walk (64 reps)',
        A2)
    box(0.1, 0.2, 4.7, 1.2, 'gates: S0 v2 (7 v1 + 300 systems: Sage = native = direct S3;\n'
        '2,375 multi-solution systems: Sage order = native order);\nnative field == Sage field in every native process;\n'
        'same counts, rows, ordered decompositions (B = N = Naa = NX);\nNX: every system == Sage; O1: run 38520305068', A3)
    box(5.1, 0.2, 4.7, 1.2, 'primary: R = mean cold CPU(B) / mean cold CPU(N),\npaired bootstrap over points;\n'
        'improvement iff 95% lower bound > 1\ncontrols: A/A in [0.95, 1.05]; planted LB > 1', A1)
    ax.set_title('Frozen design, protocol v2 (from protocol.json; not a result)', fontsize=9)
    save(fig, os.path.join(out, 'design'))


def power(out):
    p = json.load(open(os.path.join(HERE, 'analysis', 'power.json')))
    rates = p['lower_bound_above_1_rate']
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    for n, c in ((8, MUTED), (12, A2), (16, A1)):
        ds = sorted({float(k.split('delta')[1]) for k in rates})
        ax.plot(ds, [rates['n%d_delta%.2f' % (n, d)] for d in ds], 'o-', color=c, label='%d points' % n)
    ax.axhline(0.025, color=INK, lw=0.8, ls=':')
    ax.set_xscale('log')
    ax.set_xlabel('true end-to-end ratio delta (B / N)')
    ax.set_ylabel('share with 95% lower bound > 1')
    ax.set_title('Power of the frozen primary (simulated, sigma = %.2f log per process, %d sims)' %
                 (p['model']['sigma_log_per_process'], p['model']['sims']), fontsize=8.5)
    ax.legend(fontsize=7, frameon=False)
    ax.spines[['top', 'right']].set_visible(False)
    save(fig, os.path.join(out, 'power'))


def invalid(r, rd, out):
    """An invalid receipt has no primary: draw what ran and what the gates saw."""
    rows = [json.loads(l) for l in open(os.path.join(rd, 'runs.jsonl'))]
    ran = sum(1 for x in rows if x.get('status') == 'ran')
    s0 = next(g['detail'] for k, g in r['gates'].items() if k.startswith('S0 ')) or {}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 3.2), gridspec_kw={'width_ratios': [1.3, 1]})
    names = ['systems', 'Sage ==\nnative', 'direct S3 ==\nnative', 'native ==\nbrute force']
    vals = [s0.get(k) or 0 for k in ('systems', 'set_equal', 'third_equal', 'bruteforce_equal')]
    a1.bar(range(4), vals, color=[MUTED, A2, A3, A1])
    for i, v in enumerate(vals):
        a1.text(i, v + 4, str(v), ha='center', fontsize=8)
    a1.set_xticks(range(4))
    a1.set_xticklabels(names, fontsize=8)
    a1.set_ylim(0, 340)
    a1.set_title('S0 self-test', fontsize=9)
    a2.bar([0, 1], [ran, len(rows) - ran], color=[A1, MUTED])
    a2.set_xticks([0, 1])
    a2.set_xticklabels(['ran', 'not run after\nfailed S0'], fontsize=8)
    for i, v in enumerate([ran, len(rows) - ran]):
        a2.text(i, v + 1, str(v), ha='center', fontsize=8)
    a2.set_title('scheduled rows (%d)' % len(rows), fontsize=9)
    for a in (a1, a2):
        a.spines[['top', 'right']].set_visible(False)
    fig.suptitle('Protocol v2 receipt: verdict %s; no ratio exists' % r['verdict'], fontsize=9, y=1.06)
    save(fig, os.path.join(out, 'result'))


def s0_diagnosis(out):
    """Run 39307409409's S0, re-derived without Sage (diagnosis/s0_v1_rederived.json) and the
    v2 S0 systems checked locally without Sage (diagnosis/s0_v2_local.json)."""
    d1 = json.load(open(os.path.join(HERE, 'diagnosis', 's0_v1_rederived.json')))
    s1 = d1['summary']
    sg = json.load(open(os.path.join(HERE, 'diagnosis', 'sage_run_39329564781', 'sage_diag.json')))['s0_v1']['summary']
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 3.7), gridspec_kw={'width_ratios': [1.4, 1]})
    names = ['v1 native\n= S3\nover m', 'v1 native\n= S3 over\nreciprocal', 'v1 native\n= its brute\nforce',
             'fixed\nbinding\n= S3 over m', 'Sage\n= S3\nover m', 'Sage\n= fixed\nbinding']
    vals = [s1['v1_set_equal_vs_third'], s1['v1_native_equals_third_reciprocal'], s1['v1_bruteforce_equal'],
            s1['fixed_equals_third'], sg['sage_eq_third'], sg['sage_eq_native_fixed']]
    cols = [A2, A1, MUTED, A3, INK, INK]
    a1.bar(range(6), vals, color=cols)
    for i, v in enumerate(vals):
        a1.text(i, v + 5, '%d/300' % v, ha='center', fontsize=7.5)
    a1.set_xticks(range(6))
    a1.set_xticklabels(names, fontsize=6.8)
    a1.set_ylim(0, 360)
    a1.set_ylabel('S0 systems equal as sets')
    a1.set_title('Run 39307409409 S0 re-derived from its seed (bars 1-4: no Sage;\n'
                 '5-6: untimed Sage run 39329564781)', fontsize=8)
    mm = s1['mismatching_systems']
    for i, x in enumerate(mm):
        a2.plot([i], [1], 'o' if x['third'] else 'x', color=A1, ms=8)
        a2.plot([i], [0], 'o' if x['native_v1_modulus'] else 'x', color=A2, ms=8)
        lab = ' / '.join('(%d,%d)' % tuple(p) for p in (x['third'] or x['native_v1_modulus']))
        a2.text(i, 0.5, lab, ha='center', va='center', fontsize=6.5, rotation=90, color=INK)
    a2.set_xticks(range(len(mm)))
    a2.set_xticklabels(['t=%d\nj=%d' % (x['t'], x['j']) for x in mm], fontsize=6.5)
    a2.set_yticks([0, 1])
    a2.set_yticklabels(['v1 native\n(reciprocal m)', 'S3 over m\n(Sage field)'], fontsize=7)
    a2.set_ylim(-0.6, 1.6)
    a2.set_title('the 7 mismatches: o = one solution (u, w), x = empty', fontsize=8.5)
    for a in (a1, a2):
        a.spines[['top', 'right']].set_visible(False)
    fig.suptitle('Root cause: arm.sage v1 passed the reciprocal of the field modulus to the native context; '
                 'native and its brute force share it', fontsize=8.5, y=1.03)
    save(fig, os.path.join(out, 's0_diagnosis'))


def result(rd):
    r = json.load(open(os.path.join(rd, 'result.json')))
    out = os.path.join(rd, 'figures')
    os.makedirs(out, exist_ok=True)
    if 'per_point' not in r:
        invalid(r, rd, out)
        return
    pts = sorted(r['per_point'])
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    for a, c, m in (('B', A2, 'o'), ('NX', MUTED, 's'), ('N', A1, 'o'), ('Naa', A3, 'x')):
        ax.plot(range(len(pts)), [r['per_point'][p][a]['cold_cpu_s'] for p in pts], m, color=c, label=a)
    rho = r['secondary']['rho']['cpu_s_per_solve']
    ax.axhline(rho, color=INK, lw=0.8, ls='--', label='rho (mean per solve)')
    ax.set_yscale('log')
    ax.set_xticks(range(len(pts)))
    ax.set_xticklabels(pts, rotation=45, fontsize=7)
    ax.set_ylabel('cold CPU s per complete ECDLP')
    pr = r['primary']
    ax.set_title('Cold CPU per point; R = B / N = %.2f [%.2f, %.2f], verdict %s' %
                 (pr['point'], pr['lo95'], pr['hi95'], r['verdict']), fontsize=8.5)
    ax.legend(fontsize=7, frameon=False, ncol=5, loc='center', bbox_to_anchor=(0.5, -0.32))
    ax.spines[['top', 'right']].set_visible(False)
    save(fig, os.path.join(out, 'result'))


if __name__ == '__main__':
    if sys.argv[1] == 'design':
        d = os.path.join(HERE, 'figures')
        os.makedirs(d, exist_ok=True)
        baseline_phases(d)
        design(d)
        power(d)
        s0_diagnosis(d)
    else:
        result(sys.argv[2])

"""Figures for volcano-n19-native-loop-20261021 (matplotlib).

    python3 make_figures.py design          figures/{design,power,profile}.{svg,png}
                                            (from protocol.json, schedule.json, analysis/power.json, the v3
                                            archive and, when present, diagnosis/run_github_*/profile/)
    python3 make_figures.py result RECEIPT  RECEIPT/figures/result.{svg,png} (from result.json)
"""
import glob
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
V3ROWS = os.path.join(HERE, '..', 'volcano-n19-native-tau6-v3-20261020', 'run_github_39387473809', 'timed', 'panel',
                      'rows')
INK, MUTED, A1, A2, A3, A4, BAD = '#1f2933', '#7b8794', '#2f6fbd', '#d9822b', '#3f9142', '#8e5ea2', '#c0392b'


def save(fig, base):
    fig.savefig(base + '.svg', bbox_inches='tight')
    fig.savefig(base + '.png', dpi=160, bbox_inches='tight')
    plt.close(fig)


def box(ax, x, y, w, h, text, color, fs=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02', fc=color, ec=INK, lw=0.8, alpha=0.9))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=fs, color='white' if color != 'white'
            else INK, wrap=True)


def v3_n_split():
    rows = [json.load(open(os.path.join(V3ROWS, n))) for n in sorted(os.listdir(V3ROWS))]
    n = [r for r in rows if r['arm'] == 'N']
    m = lambda k: sum(r[k] for r in n) / len(n)
    return {'setup': m('setup_cpu_s'), 'native solve (ctypes)': m('gb_cpu_s'),
            'rest of relation loop': m('relation_cpu_s') - m('gb_cpu_s'), 'linear algebra': m('linalg_cpu_s'),
            'tauEigen + GF(r)': m('online_cpu_s') - m('total_cpu_s')}, len(n)


def runner_profile():
    files = sorted(glob.glob(os.path.join(HERE, 'diagnosis', 'run_github_*', 'profile', 'timers-*.json')))
    recs = [json.load(open(f)) for f in files]
    recs = [r for r in recs if r.get('instrumented_reproduces_plain')]
    if not recs:
        return None, None
    stages = {}
    for r in recs:
        for k, v in r['instrumented']['stages_cpu_s'].items():
            stages[k] = stages.get(k, 0.0) + v / len(recs)
    start = None
    sp = sorted(glob.glob(os.path.join(HERE, 'diagnosis', 'run_github_*', 'profile', 'startup.json')))
    if sp:
        start = json.load(open(sp[-1]))['summary']
    return {'stages': stages, 'points': len(recs),
            'plain_cold': sum(r['plain']['cold_cpu_s'] for r in recs) / len(recs),
            'instr_cold': sum(r['instrumented']['cold_cpu_s'] for r in recs) / len(recs)}, start


def profile(out):
    split, nrows = v3_n_split()
    prof, start = runner_profile()
    ncol = 3 if prof else 2
    fig, axes = plt.subplots(1, ncol, figsize=(4.6 * ncol, 4.2))
    ax = axes[0]
    labels = list(split)
    vals = [split[k] * 1e3 for k in labels]
    cols = [A2, A1, BAD, A3, MUTED]
    bottom = 0
    for lab, v, c in zip(labels, vals, cols):
        ax.bar([0], [v], bottom=bottom, color=c, label='%s %.1f ms' % (lab, v))
        bottom += v
    ax.set_xticks([0])
    ax.set_xticklabels(['arm N (v3 run 39387473809,\n%d processes, mean)' % nrows], fontsize=7)
    ax.set_ylabel('cold CPU ms per ECDLP (in-process)')
    ax.set_title('Baseline N: archived phase timers', fontsize=9)
    ax.legend(fontsize=6.5, frameon=False, loc='upper right')
    ax.set_xlim(-0.6, 1.6)
    ax.spines[['top', 'right']].set_visible(False)
    if prof:
        ax = axes[1]
        st = sorted(prof['stages'].items(), key=lambda kv: -kv[1])
        ax.barh(range(len(st)), [v * 1e3 for _, v in st], color=[A2 if k.startswith('setup') else
                                                                 A1 if 'native_solve' in k else
                                                                 A3 if 'linalg' in k else BAD for k, _ in st])
        ax.set_yticks(range(len(st)))
        ax.set_yticklabels([k for k, _ in st], fontsize=6)
        ax.invert_yaxis()
        ax.set_xlabel('CPU ms per ECDLP (mean of %d points)' % prof['points'], fontsize=8)
        ax.set_title('Baseline N on the runner: instrumented stages\n(untimed diagnostic; nested stages overlap)',
                     fontsize=8)
        ax.spines[['top', 'right']].set_visible(False)
    ax = axes[-1]
    ax.bar([0], [split[k] * 1e3 for k in ['setup']], color=A2)
    est = split['native solve (ctypes)'] * 1e3
    ax.bar([1], [est], color=A1)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['N setup\n(removed)', 'N native solve\n(kept in N2)'], fontsize=7)
    title = 'What N2 keeps'
    if start:
        k = 'sage profile_n.sage --mode load (v3 arm loads)'
        if k in start:
            ax.bar([2], [start[k]['child_cpu_s_mean'] * 1e3], color=MUTED)
            ax.set_xticks([0, 1, 2])
            ax.set_xticklabels(['N setup\n(removed)', 'N native solve\n(kept in N2)',
                                'Sage start-up + loads\n(outside the primary)'], fontsize=7)
    ax.set_title(title + ' (locally the v3 solve is about 96% of N2)', fontsize=8)
    ax.set_ylabel('CPU ms')
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    save(fig, os.path.join(out, 'profile'))


def design(out):
    proto = json.load(open(os.path.join(HERE, 'protocol.json')))
    sched = json.load(open(os.path.join(HERE, 'schedule.json')))
    d = proto['design']
    fig = plt.figure(figsize=(11, 7.2))
    ax = fig.add_axes([0, 0.45, 1, 0.55])
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 5)
    ax.axis('off')
    ax.text(0.1, 4.75, 'Port scope: what moves out of Sage', fontsize=11, color=INK, weight='bold')
    box(ax, 0.2, 3.2, 3.2, 1.2, 'Baseline N (Sage process)\nSage start-up + loads\nsetup: GF, TauCurve, lift_x,\n'
        'generator\ntauDlp loop in Python/Sage', A2, 7.5)
    box(ax, 0.2, 2.2, 3.2, 0.8, 'v3 native per-shift solve\n(ctypes, ~5,400 calls)', A1, 7.5)
    box(ax, 0.2, 1.2, 3.2, 0.8, 'Sage sparse matrix,\nleft_kernel, log', A3, 7.5)
    ax.annotate('', xy=(4.3, 2.8), xytext=(3.5, 2.8), arrowprops=dict(arrowstyle='->', color=INK, lw=1.5))
    box(ax, 4.4, 3.2, 3.2, 1.2, 'Candidate N2 (tau6dlp, no Sage)\nsetup natively; CPython MT19937\n'
        'targets; affine E arithmetic;\nshift loop and checks', A4, 7.5)
    box(ax, 4.4, 2.2, 3.2, 0.8, 'the same v3 solve source\n(included by path)', A1, 7.5)
    box(ax, 4.4, 1.2, 3.2, 0.8, 'GF(r) reduced echelon\nleft kernel (Sage basis), log', A3, 7.5)
    box(ax, 7.9, 1.2, 3.0, 3.2, 'Exactness checks\nS0 (lib) + S0b (binary)\nO1 / O2 vs archive\nper point: counts, log,\n'
        'ordered relations,\ndigests, reps identical\nacross B, N, N2, N2aa, N2X\nN2X: Sage path alongside,\n'
        'every target, shift order,\nrelation and kernel vector', MUTED, 7.2)
    ax.text(0.2, 0.6, 'Primary: sum cold CPU(N) / sum cold CPU(N2), in-process (setup + online), %d points x %d '
            'alternating pairs, two-stage paired bootstrap 95%%.\nKey secondary (process-inclusive): child CPU N / N2 '
            '(includes Sage start-up). Controls: A/A N2/N2aa in [0.95, 1.05] (%d x %d); planted N2X/N2 LB > 1 '
            '(%d x %d).' % (d['points'], d['primary_pairs_per_point'], d['points'], d['aa_pairs_per_point'],
                            d['points'], d['planted_pairs_per_point']), fontsize=7.5, color=INK)
    ax2 = fig.add_axes([0.05, 0.05, 0.9, 0.36])
    segs = [s for s in sched['parts']['timed']['segments'] if s['kind'] == 'point']
    color = {'N': A2, 'N2': A4, 'N2aa': A3, 'N2X': MUTED, 'B': BAD, 'rho': INK}
    for i, s in enumerate(segs):
        for j, r in enumerate(s['runs']):
            c = color[r['arm']]
            ax2.add_patch(plt.Rectangle((j, i), 0.9, 0.8, color=c, alpha=0.55 if r.get('warm') else 0.95))
    ax2.set_xlim(0, max(len(s['runs']) for s in segs))
    ax2.set_ylim(len(segs), 0)
    ax2.set_yticks([i + 0.4 for i in range(len(segs))])
    ax2.set_yticklabels([s['id'] for s in segs], fontsize=5.5)
    ax2.set_xlabel('position in the point segment (fresh pinned process each)', fontsize=8)
    ax2.set_title('Frozen timed order (schedule.json; not a result): after S0, S0b, O1, O2', fontsize=9)
    for k, c in color.items():
        ax2.bar([0], [0], color=c, label=k)
    ax2.legend(ncol=6, fontsize=7, frameon=False, loc='upper center', bbox_to_anchor=(0.5, -0.2))
    save(fig, os.path.join(out, 'design'))


def power(out):
    p = json.load(open(os.path.join(HERE, 'analysis', 'power.json')))
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for sigma, c in zip(p['sigmas_log_per_process'], (A1, A2, BAD)):
        ys = [p['lower_bound_above_1_rate']['v3_N_cold_cpu_per_point_sigma%.2f_delta%.2f' % (sigma, dd)]
              for dd in p['deltas']]
        ax.plot(p['deltas'], ys, 'o-', color=c, label='sigma %.2f per process' % sigma)
    ax.axvline(p['min_delta'], color=MUTED, ls=':', lw=1)
    ax.set_xlabel('true ratio N / N2 (delta)')
    ax.set_ylabel('share of panels with 95% LB > 1')
    ax.set_title('Power of the frozen primary (simulated, %d points x %d pairs)' %
                 (p['design']['points'], p['design']['primary_pairs_per_point']), fontsize=9)
    ax.legend(fontsize=7, frameon=False)
    ax.spines[['top', 'right']].set_visible(False)
    save(fig, os.path.join(out, 'power'))


def result(receipt):
    res = json.load(open(os.path.join(receipt, 'result.json')))
    st = res['statistics']
    out = os.path.join(receipt, 'figures')
    os.makedirs(out, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), gridspec_kw={'width_ratios': [2.2, 1]})
    ax = axes[0]
    pts = sorted({r['point'] for r in st.get('per_pair', [])})
    for r in st.get('per_pair', []):
        ax.plot(pts.index(r['point']), r['ratio'], 'o', ms=3.5, color=A1 if r['first'] == 'N' else A2, alpha=0.8)
    p = st.get('primary_cold_cpu_N_over_N2')
    if p:
        ax.axhline(p['estimate'], color=INK, lw=1)
        ax.axhspan(p['ci95'][0], p['ci95'][1], color=MUTED, alpha=0.25)
    ax.set_xticks(range(len(pts)))
    ax.set_xticklabels(pts, rotation=60, fontsize=6)
    ax.set_ylabel('cold CPU N / N2 per pair')
    ax.set_title('Primary pairs (blue: N first, orange: N2 first); verdict %s' % res['verdict'], fontsize=9)
    ax.spines[['top', 'right']].set_visible(False)
    ax = axes[1]
    keys = [('primary_cold_cpu_N_over_N2', 'primary N/N2'), ('child_cpu_N_over_N2', 'child CPU N/N2'),
            ('launcher_wall_N_over_N2', 'launcher wall N/N2'), ('planted_cold_cpu_N2X_over_N2', 'planted N2X/N2'),
            ('aa_cold_cpu_N2_over_N2aa', 'A/A N2/N2aa')]
    for i, (k, lab) in enumerate(keys):
        e = st.get(k)
        if e:
            ax.errorbar([e['estimate']], [i], xerr=[[e['estimate'] - e['ci95'][0]], [e['ci95'][1] - e['estimate']]],
                        fmt='o', color=A1 if i < 3 else MUTED, capsize=3)
    ax.axvline(1, color=BAD, ls=':', lw=1)
    ax.set_xscale('log')
    ax.set_yticks(range(len(keys)))
    ax.set_yticklabels([lab for _, lab in keys], fontsize=7)
    ax.set_title('Estimates [95%, two-stage paired bootstrap]', fontsize=9)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    save(fig, os.path.join(out, 'result'))


def main():
    if sys.argv[1] == 'design':
        out = os.path.join(HERE, 'figures')
        os.makedirs(out, exist_ok=True)
        profile(out)
        design(out)
        power(out)
    elif sys.argv[1] == 'result':
        result(sys.argv[2])


if __name__ == '__main__':
    main()

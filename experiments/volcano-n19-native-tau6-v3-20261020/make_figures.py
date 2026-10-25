"""Figures for volcano-n19-native-tau6-v3-20261020 (matplotlib), protocol v3.

    python3 make_figures.py design          figures/{design,power,crash_diagnosis,baseline_phases}.{svg,png}
                                            (before any run; from protocol.json, schedule.json,
                                            analysis/power.json and diagnosis/emulate_preparser.json)
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
INK, MUTED, A1, A2, A3, BAD = '#1f2933', '#7b8794', '#2f6fbd', '#d9822b', '#3f9142', '#c0392b'
ARM_COLOR = {'B': A2, 'N': A1, 'Naa': A3, 'NX': MUTED, 'rho': INK, 'selftest': '#9aa5b1', 'O': '#9aa5b1'}


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
    proto = json.load(open(os.path.join(HERE, 'protocol.json')))
    sched = json.load(open(os.path.join(HERE, 'schedule.json')))
    d = proto['design']
    fig = plt.figure(figsize=(10.4, 6.6))
    ax = fig.add_axes([0, 0.42, 1, 0.58])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis('off')

    def box(x, y, w, h, text, c, fs=7.2):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.05', fc='white', ec=c, lw=1.4))
        ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=fs, color=INK)

    box(0.1, 3.3, 3.0, 1.5, 'job sage-smoke (UNTIMED gate)\ncargo test + build (Rust 1.99.0)\nverifier corruption tests\n'
        'v2 crash reproduced (recorded)\nsmoke part: S0, O1, v2 p00 + p01\nthrough B, N, Naa, NX, rho', A3)
    box(3.6, 3.3, 3.0, 1.5, 'smoke gate = %d gates, re-derived\nfrom raw rows by the verifier\n(raw digests, schedule identity,\n'
        'recomputed relation digests,\nB = N = Naa = NX per point)' % len(proto['gates_required']['smoke']), A3)
    box(7.1, 3.3, 2.8, 1.5, 'job timed (needs sage-smoke,\nsame library digest)\nS0 (2,982 systems), O1 (10 digests)\n'
        '%d points x (%d B/N + %d N/Naa\n+ %d NX/N pairs + rho)' % (d['points'], d['primary_pairs_per_point'],
                                                             d['aa_pairs_per_point'], d['planted_pairs_per_point']), A1)
    ax.annotate('', xy=(3.6, 4.05), xytext=(3.1, 4.05), arrowprops=dict(arrowstyle='->', color=MUTED))
    ax.annotate('', xy=(7.1, 4.05), xytext=(6.6, 4.05), arrowprops=dict(arrowstyle='->', color=MUTED))
    box(0.1, 1.2, 4.8, 1.6, 'primary: R = sum cold CPU(B) / sum cold CPU(N) over %d pairs\n'
        'two-stage paired bootstrap (points, then pairs), %d draws\nimprovement iff 95%% lower bound > 1\n'
        'controls: A/A N/Naa estimate in [%.2f, %.2f]; planted NX/N LB > 1' % (
            d['points'] * d['primary_pairs_per_point'], proto['statistics']['bootstrap_draws'],
            proto['controls']['aa_window'][0], proto['controls']['aa_window'][1]), A1)
    box(5.1, 1.2, 4.8, 1.6, 'per run (Tier 1 records): placement (Cpus_allowed_list + arm affinity),\n'
        '/proc/schedstat + /proc/stat, getrusage, isolated_bench counters + noise,\nlibrary digest before/after; '
        'host_cpu_record at start/end\nverdict invalid on any false, missing or unknown gate (%d)' %
        len(proto['gates_required']['timed']), A2)
    box(0.1, 0.1, 9.8, 0.75, 'the fix: relation_digests moved to relation_digest.py (plain Python, never preparsed); every row '
        'serialized strictly (no str() fallback);\nrows print raw_b64 + SHA-256; IC rows and O1 record raw relations so '
        'each digest is recomputed', BAD, 7)
    ax.set_title('Frozen design, protocol v3 (from protocol.json and schedule.json; not a result)', fontsize=9.5)
    ax2 = fig.add_axes([0.06, 0.04, 0.9, 0.33])
    segs = [s for s in sched['parts']['timed']['segments'] if s['kind'] == 'point']
    for yi, seg in enumerate(segs):
        for xi, r in enumerate(seg['runs']):
            ax2.add_patch(plt.Rectangle((xi, yi), 0.92, 0.8, color=ARM_COLOR[r['arm']]))
    ax2.set_xlim(0, max(len(s['runs']) for s in segs))
    ax2.set_ylim(len(segs), 0)
    ax2.set_yticks([i + 0.4 for i in range(len(segs))])
    ax2.set_yticklabels([s['point'] for s in segs], fontsize=6)
    ax2.set_xlabel('run order within the point segment (one fresh pinned Sage process each)', fontsize=8)
    ax2.set_xticks([])
    for a, c in ARM_COLOR.items():
        if a in ('selftest', 'O'):
            continue
        ax2.plot([], [], 's', color=c, label=a)
    ax2.legend(fontsize=7, frameon=False, ncol=5, loc='lower center', bbox_to_anchor=(0.5, 1.0))
    ax2.set_title('The frozen timed run order (schedule.json): seeded block starts and shuffled block order per point',
                  fontsize=8.5, pad=16)
    for s in ax2.spines.values():
        s.set_visible(False)
    save(fig, os.path.join(out, 'design'))


def power(out):
    p = json.load(open(os.path.join(HERE, 'analysis', 'power.json')))
    rates = p['lower_bound_above_1_rate']
    fig, ax = plt.subplots(figsize=(6.6, 3.3))
    for prior, ls in (('v2_runner', '-'), ('archived', '--')):
        for sigma, c in ((0.10, A1), (0.20, A2)):
            ds = p['deltas']
            ax.plot(ds, [rates['%s_sigma%.2f_delta%.2f' % (prior, sigma, dd)] for dd in ds], 'o' + ls, color=c,
                    label='prior %s, sigma %.2f' % (prior, sigma), ms=4)
    ax.axhline(0.025, color=INK, lw=0.8, ls=':')
    ax.set_xlabel('true end-to-end ratio delta (B / N)')
    ax.set_ylabel('share with 95% lower bound > 1')
    ax.set_title('Power of the frozen primary: %d points x %d pairs, two-stage bootstrap (%d sims each)' %
                 (p['design']['points'], p['design']['primary_pairs_per_point'], p['design']['sims']), fontsize=8.5)
    ax.legend(fontsize=7, frameon=False)
    ax.spines[['top', 'right']].set_visible(False)
    save(fig, os.path.join(out, 'power'))


def crash_diagnosis(out):
    e = json.load(open(os.path.join(HERE, 'diagnosis', 'emulate_preparser.json')))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 3.4), gridspec_kw={'width_ratios': [1.25, 1]})
    a1.set_xlim(0, 10)
    a1.set_ylim(0, 4)
    a1.axis('off')
    steps = [('ordered = [[list(map(int, t)) ...]]', 'json.dumps OK', A3),
             ('canon = [sorted(r) for r in ordered]', 'json.dumps OK', A3),
             ('row.get(col, 0) + sg*pow(...) % int(p)\n0 -> Integer(0) (preparser)', 'TypeError: Integer', BAD)]
    for i, (code, res, c) in enumerate(steps):
        y = 3.0 - 1.15 * i
        a1.add_patch(FancyBboxPatch((0.1, y), 6.0, 0.8, boxstyle='round,pad=0.04', fc='white', ec=c, lw=1.3))
        a1.text(3.1, y + 0.4, code, ha='center', va='center', fontsize=7, family='monospace')
        a1.text(6.4, y + 0.4, res, ha='left', va='center', fontsize=7.5, color=c)
    a1.set_title('v2 arm.sage relation_digests, in the order it ran (traceback: h(rows))', fontsize=8.5)
    labels = ['v2, plain\nPython', 'v2, integer\nliterals ->\nInteger', 'v3 module,\nint inputs', 'v3 module,\nInteger inputs']
    ok = [True, e['v2_preparsed']['raised'] is None, True, e['v3_equals_v2_plain']]
    a2.bar(range(4), [1] * 4, color=[A3 if o else BAD for o in ok])
    for i, o in enumerate(ok):
        a2.text(i, 0.5, 'digests\nequal' if (o and i != 1) else ('OK' if o else 'TypeError'), ha='center', va='center',
                fontsize=7.5, color='white')
    a2.set_xticks(range(4))
    a2.set_xticklabels(labels, fontsize=7)
    a2.set_yticks([])
    a2.set_title('local emulation on v2 point p00 (%d relations; no Sage)' % e['relations'], fontsize=8.5)
    for s in a2.spines.values():
        s.set_visible(False)
    fig.suptitle('Root cause of run 39376405326: the Sage preparser made the default 0 a Sage Integer; '
                 'json.dumps refused the rows digest', fontsize=9, y=1.03)
    save(fig, os.path.join(out, 'crash_diagnosis'))


def result(rd):
    r = json.load(open(os.path.join(rd, 'result.json')))
    out = os.path.join(rd, 'figures')
    os.makedirs(out, exist_ok=True)
    st = r.get('statistics', {})
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 3.8), gridspec_kw={'width_ratios': [1.5, 1]})
    pp = st.get('per_pair') or []
    pts = sorted({x['point'] for x in pp})
    for x in pp:
        a1.plot(pts.index(x['point']) + (x['pair'] - 2) * 0.18, x['ratio'], 'o' if x['first'] == 'B' else 's',
                color=A1 if x['first'] == 'B' else A2, ms=4)
    pr = st.get('primary_cold_cpu_B_over_N')
    if pr:
        a1.axhspan(pr['ci95'][0], pr['ci95'][1], color=A1, alpha=0.15)
        a1.axhline(pr['estimate'], color=A1, lw=1)
    a1.set_xticks(range(len(pts)))
    a1.set_xticklabels(pts, rotation=45, fontsize=6.5)
    a1.set_ylabel('cold CPU B / N per pair')
    a1.plot([], [], 'o', color=A1, label='B first')
    a1.plot([], [], 's', color=A2, label='N first')
    a1.legend(fontsize=7, frameon=False)
    a1.set_title('R = %s, verdict %s' % ('%.2f [%.2f, %.2f]' % (pr['estimate'], *pr['ci95']) if pr else 'n/a',
                                        r['verdict']), fontsize=8.5)
    g = r.get('gates', {})
    names = sorted(g)
    a2.barh(range(len(names)), [1] * len(names), color=[A3 if g[k] is True else BAD for k in names])
    a2.set_yticks(range(len(names)))
    a2.set_yticklabels(names, fontsize=5.5)
    a2.set_xticks([])
    a2.set_title('gates (green = true); controls: %s' % json.dumps(r.get('controls')), fontsize=6.5)
    for a in (a1, a2):
        a.spines[['top', 'right']].set_visible(False)
    save(fig, os.path.join(out, 'result'))


if __name__ == '__main__':
    if sys.argv[1] == 'design':
        d = os.path.join(HERE, 'figures')
        os.makedirs(d, exist_ok=True)
        baseline_phases(d)
        design(d)
        power(d)
        crash_diagnosis(d)
    else:
        result(sys.argv[2])

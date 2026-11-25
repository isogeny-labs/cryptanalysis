#!/usr/bin/env python3
"""Render the handbook idea catalogue: IDEAS.md, diagram SVG, HTML and PDF.

Reads ideas.json (the 100 selected ideas), formal-results.json (Lean module
records), critic.json and prior-art pool.json; writes IDEAS.md, the
chapter-by-phase heatmap (diagram.svg) and ideas-per-phase bar (phases.svg),
then report.html via pandoc and report.pdf via the pre-installed Chromium.
Pure standard library plus pandoc and playwright; no matplotlib.
"""
import json, pathlib, re, subprocess, sys, collections, html

HERE = pathlib.Path(__file__).resolve().parent
ideas = json.loads((HERE / 'ideas.json').read_text())
formal = json.loads((HERE / 'formal-results.json').read_text()) if (HERE / 'formal-results.json').exists() else []
critic = json.loads((HERE / 'critic.json').read_text()) if (HERE / 'critic.json').exists() else {}
pool = json.loads((HERE / 'pool.json').read_text()) if (HERE / 'pool.json').exists() else []

PHASES = ['factor-base','decomposition','relation-collection','relation-filtering','linear-algebra','descent','cost-model','curve-selection','hardware']

def chapter(sec):
    m = re.match(r'\s*(\d+)', sec or '')
    return int(m.group(1)) if m else None

# Lean status per idea id.
lean = {}
for b in formal:
    if not b: continue
    f = b.get('formal') or {}
    v = b.get('verify') or {}
    for rec in f.get('ideas', []):
        lean[rec['id']] = {'file': f.get('file',''), 'claim_decl': rec['claim_decl'], 'theorems': rec['theorems'],
                           'status': rec['status'], 'missing_bridge': rec['missing_bridge'],
                           'verified': bool(v.get('pass')), 'repaired': bool(b.get('repaired'))}

# --- heatmap chapter x phase ---
chap_counts = collections.Counter()
cells = collections.Counter()
for i in ideas:
    chs = {chapter(s) for s in i['handbook_sections']} - {None}
    for c in chs:
        cells[(c, i['ic_phase'])] += 1
        chap_counts[c] += 1
chapters = sorted({c for (c, _) in cells})
cw, chh, left, top = 86, 26, 170, 60
W = left + cw * len(PHASES) + 20
H = top + chh * len(chapters) + 60
mx = max(cells.values()) if cells else 1
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="Helvetica, Arial, sans-serif" font-size="11">',
       f'<rect width="{W}" height="{H}" fill="white"/>',
       f'<text x="{left}" y="22" font-size="14" font-weight="bold">Handbook of Finite Fields chapter × index-calculus phase: ideas per cell (n = {len(ideas)}; an idea citing two chapters counts in both)</text>']
for j, p in enumerate(PHASES):
    svg.append(f'<text x="{left + cw*j + cw/2}" y="{top-8}" text-anchor="middle" font-size="10">{p}</text>')
for r, c in enumerate(chapters):
    svg.append(f'<text x="{left-6}" y="{top + chh*r + chh/2 + 4}" text-anchor="end">ch {c} ({chap_counts[c]})</text>')
    for j, p in enumerate(PHASES):
        n = cells[(c, p)]
        shade = 255 - int(175 * n / mx) if n else 255
        fill = f'rgb({shade},{shade},255)' if n else 'rgb(245,245,245)'
        svg.append(f'<rect x="{left + cw*j}" y="{top + chh*r}" width="{cw-2}" height="{chh-2}" fill="{fill}" stroke="#ccc"/>')
        if n: svg.append(f'<text x="{left + cw*j + cw/2 - 1}" y="{top + chh*r + chh/2 + 4}" text-anchor="middle">{n}</text>')
svg.append(f'<text x="{left}" y="{H-30}" font-size="10">Source: ideas.json (selected catalogue, 2026-11-03). Counts are catalogue entries, not measurements; no idea here is verified or measured.</text>')
svg.append('</svg>')
(HERE / 'diagram.svg').write_text('\n'.join(svg))

# --- bar: ideas per phase with Lean status ---
pc = collections.Counter(i['ic_phase'] for i in ideas)
proved = collections.Counter(i['ic_phase'] for i in ideas if lean.get(i['id'], {}).get('status') == 'proved-support' and lean.get(i['id'], {}).get('verified'))
bw, bh, lft, tp = 70, 180, 60, 40
W2 = lft + bw * len(PHASES) + 40; H2 = tp + bh + 70
m2 = max(pc.values()) if pc else 1
s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W2}" height="{H2}" font-family="Helvetica, Arial, sans-serif" font-size="11">', f'<rect width="{W2}" height="{H2}" fill="white"/>',
     f'<text x="{lft}" y="20" font-size="13" font-weight="bold">Ideas per IC phase (dark: verified Lean supporting theorem; light: Prop stated only or unverified)</text>']
for j, p in enumerate(PHASES):
    n, k = pc[p], proved[p]
    hN = bh * n / m2; hK = bh * k / m2
    x = lft + bw*j + 10
    s.append(f'<rect x="{x}" y="{tp + bh - hN}" width="{bw-20}" height="{hN}" fill="#b9c6ff"/>')
    s.append(f'<rect x="{x}" y="{tp + bh - hK}" width="{bw-20}" height="{hK}" fill="#2b47c9"/>')
    s.append(f'<text x="{x + (bw-20)/2}" y="{tp + bh - hN - 4}" text-anchor="middle">{n} ({k})</text>')
    s.append(f'<text x="{x + (bw-20)/2}" y="{tp + bh + 14}" text-anchor="middle" font-size="9">{p}</text>')
s.append(f'<line x1="{lft}" y1="{tp+bh}" x2="{W2-30}" y2="{tp+bh}" stroke="#444"/>')
s.append(f'<text x="{lft}" y="{H2-20}" font-size="10">Unit: catalogue entries. Lean theorems are supporting lemmas in core Lean 4 (no Mathlib); none proves an ECDLP speedup.</text>')
s.append('</svg>')
(HERE / 'phases.svg').write_text('\n'.join(s))

# --- IDEAS.md ---
def esc(t): return (t or '').replace('|', '\\|').replace('\n', ' ')
out = ['# 100 index-calculus ideas from the Handbook of Finite Fields (2026-11-03)', '',
       'Each row is a proposal: mechanism, falsifiable claim, preregistered prediction, cheapest discriminating test, falsifier, prior-art status in this lab, and its Lean declaration. Nothing in this table is verified, measured or an improvement; a row becomes a success only when a frozen, replayed measurement lowers cost against the named IC baseline (AGENTS.md, success criterion).', '',
       f'Lean status key: `proved` = a supporting theorem compiled and passed the axiom audit; `stated` = only the claim `Prop` exists; `unverified` = the module failed the mechanical check (see `formal/receipts/`).', '']
for p in PHASES:
    rows = [i for i in ideas if i['ic_phase'] == p]
    if not rows: continue
    out += [f'## {p} ({len(rows)})', '']
    for i in rows:
        L = lean.get(i['id'])
        st = 'unverified' if not L else ('proved' if (L['status']=='proved-support' and L['verified']) else ('stated' if L['verified'] else 'unverified'))
        out += [f"### {i['id']} — {i['title']}", '',
                f"- **Handbook**: {', '.join(i['handbook_sections'])}  ·  **Prior art**: {i['prior_art_status']}  ·  **Lean**: {st}" + (f" (`{L['claim_decl']}`; theorems: {', '.join('`'+t+'`' for t in L['theorems']) or 'none'})" if L else ''),
                f"- **Claim**: {i['claim']}",
                f"- **Prediction**: {i['prediction']}",
                f"- **Cheapest test**: {i['cheapest_test']}",
                f"- **Falsifier**: {i['falsifier']}",]
        if L and L.get('missing_bridge'): out.append(f"- **Lean gap (assumed, not proved)**: {L['missing_bridge']}")
        if i.get('merged_from'): out.append(f"- Merged from pool keys: {', '.join(i['merged_from'])}")
        out.append('')
(HERE / 'IDEAS.md').write_text('\n'.join(out))
print('wrote IDEAS.md, diagram.svg, phases.svg; ideas', len(ideas), 'lean records', len(lean))

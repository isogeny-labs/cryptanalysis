#!/usr/bin/env python3
"""Render the exact path partition from result.json as an editable SVG report."""
import json
from pathlib import Path

here = Path(__file__).resolve().parent
r = json.loads((here / 'result.json').read_text())
assert r['tracked_lean_files'] == 184
assert r['historical_receipt_sources'] + r['native_admitted_additions'] + r['tool_tree_sources_outside_corpus'] == 184
parts = [
    ('90 archived byte-identical', 90, '#2563a6'),
    ('7 fresh receipt', 7, '#25a4a8'),
    ('77 additional native', 77, '#3b9858'),
    ('10 tool-tree', 10, '#8b929d'),
]
x = 72
bars = []
for title, count, color in parts:
    width = 816 * count / 184
    bars.append(f'<rect x="{x:.2f}" y="180" width="{width:.2f}" height="68" fill="{color}"/>')
    x += width
legend = []
for i, (title, count, color) in enumerate(parts):
    y = 285 + i * 42
    legend.append(f'<rect x="72" y="{y-16}" width="21" height="21" fill="{color}"/><text x="108" y="{y}" class="body">{title} Lean source paths</text>')
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="650" viewBox="0 0 960 650">
<style>text {{font-family:DejaVu Sans,Arial,sans-serif;fill:#182638}} .title {{font-size:28px;font-weight:bold}} .sub {{font-size:17px}} .body {{font-size:18px}} .small {{font-size:14px}} .label {{font-size:20px;font-weight:bold}}</style>
<rect width="960" height="650" fill="#ffffff"/>
<text x="72" y="65" class="title">Cryptanalysis Lean source gate</text>
<text x="72" y="99" class="sub">Pinned 31 October tree: 184 tracked Lean files</text>
<text x="72" y="145" class="label">97-source receipt + 77 further native checks + 10 tool-tree sources</text>
{''.join(bars)}
{''.join(legend)}
<text x="72" y="480" class="small">Hosted corpus job 41077865188 passed at 5939def0; its log ends with “native added theorem modules checked: 77”.</text>
<text x="72" y="506" class="small">All 184 Lean path/blob IDs and {r['protected_input_paths_unchanged']} gate and dependency inputs match current d3673ee0.</text>
<text x="72" y="548" class="small">Tool-tree group: 7 selftest examples, 2 audit modules, 1 TransferAudit source outside this corpus gate.</text>
<text x="72" y="584" class="small">A native build and axiom gate checks source execution at pinned inputs. Theorem meaning and historical runs</text>
<text x="72" y="607" class="small">retain separate review obligations. Counts refer to source paths, not distinct scientific claims.</text>
</svg>'''
(here / 'scope.svg').write_text(svg)

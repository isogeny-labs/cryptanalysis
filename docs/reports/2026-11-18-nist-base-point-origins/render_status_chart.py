#!/usr/bin/env python3
"""Render the provenance-status counts as an editable SVG bar chart."""

from __future__ import annotations

import csv
from pathlib import Path


HERE = Path(__file__).resolve().parent
rows = list(csv.DictReader((HERE / "status-counts.csv").open()))
width, height = 820, 330
left, top, bar_height, gap, scale = 250, 55, 38, 24, 72
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
    '<rect width="100%" height="100%" fill="white"/>',
    '<style>text{font-family:DejaVu Sans,sans-serif;fill:#172033}.label{font-size:15px}.value{font-size:14px;font-weight:bold}.title{font-size:20px;font-weight:bold}.legend{font-size:13px}</style>',
    '<text x="20" y="28" class="title">Base-point provenance status (20 points)</text>',
]
for index, row in enumerate(rows):
    y = top + index * (bar_height + gap)
    recovered = int(row["recovered_gx"])
    unknown = int(row["unknown_origin"])
    parts.append(f'<text x="20" y="{y + 25}" class="label">{row["group"]}</text>')
    if recovered:
        w = recovered * scale
        parts.append(f'<rect x="{left}" y="{y}" width="{w}" height="{bar_height}" rx="4" fill="#22c55e"/>')
        parts.append(f'<text x="{left + w / 2}" y="{y + 25}" text-anchor="middle" class="value" fill="white">{recovered}</text>')
    if unknown:
        w = unknown * scale
        parts.append(f'<rect x="{left}" y="{y}" width="{w}" height="{bar_height}" rx="4" fill="#f59e0b"/>')
        parts.append(f'<text x="{left + w / 2}" y="{y + 25}" text-anchor="middle" class="value">{unknown}</text>')
parts.extend([
    '<rect x="250" y="303" width="14" height="14" fill="#22c55e"/><text x="272" y="315" class="legend">Gx source recovered</text>',
    '<rect x="455" y="303" width="14" height="14" fill="#f59e0b"/><text x="477" y="315" class="legend">base-point origin unknown</text>',
    '</svg>',
])
(HERE / "status-chart.svg").write_text("\n".join(parts) + "\n")

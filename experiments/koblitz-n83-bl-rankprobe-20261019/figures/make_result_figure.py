#!/usr/bin/env python3
"""Write figures/result.tex from a run's result.json and render it to PDF and PNG.

Usage: python3 figures/make_result_figure.py run_github_<id>/result.json

Ratios with 95% bootstrap intervals on a log2 axis; the dashed line is parity.
The primary G is orange, the other ratios blue, the A/A controls grey. Every
number is read from result.json (statistics block); nothing is typed here.
Requires pdflatex (TikZ) and pdftoppm.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROWS = [
    ("PRIMARY online gap G = cP / BL", "primary_online_gap_cP_over_BL", "p"),
    ("online rho (rT) / BL", "rho_online_over_BL", ""),
    ("online gap IC (cP) / rT770", "online_gap_cP_over_rT", ""),
    ("online gap BL / rT770", "online_gap_BL_over_rT", ""),
    ("end-to-end cold gap IC / rT770", "e2e_cold_gap_IC_over_rT", ""),
    ("end-to-end cold gap BL / rT770", "cold_gap_BL_over_rT", ""),
    ("cold IC / BL (about 1 by construction)", "cold_ic_over_bl", ""),
    ("A/A cold cP / cPaa", "aa_ic_cold_cP_over_cPaa", "c"),
    ("A/A online cP / cPaa", "aa_ic_online_cP_over_cPaa", "c"),
    ("A/A online BL / BLaa (geometric)", "aa_bl_online_geo_BL_over_BLaa", "c"),
]
LO, HI = -8, 8


def fmt(v):
    return "%.4g" % v


def main():
    result = json.loads(Path(sys.argv[1]).read_text())
    stats = result["statistics"]
    out = [
        "%% Editable source for result.pdf, written by make_result_figure.py from result.json",
        r"\documentclass[tikz,border=6pt]{standalone}",
        r"\usepackage[T1]{fontenc}",
        r"\begin{document}",
        r"\begin{tikzpicture}[font=\sffamily\footnotesize,x=7mm,y=-5.6mm]",
    ]
    n = len(ROWS)
    for k in range(LO, HI + 1, 2):
        out.append(r"\draw[gray!35] (%d,-0.6) -- (%d,%.1f); \node[gray] at (%d,%.1f) {%s};"
                   % (k, k, n - 0.4, k, n, fmt(2.0 ** k)))
    out.append(r"\draw[red!70!black,dashed] (0,-0.6) -- (0,%.1f);" % (n - 0.4))
    out.append(r"\node at (0,%.1f) {ratio (log scale); bars: estimate; whiskers: 95\%% bootstrap (%d cold points)};"
               % (n + 1.2, stats["complete_points"]))
    out.append(r"\node[anchor=west,font=\sffamily\bfseries] at (-24,-1.5) {Reading: %s};"
               % result["decision"].replace("_", r"\_"))
    for i, (label, key, kind) in enumerate(ROWS):
        s = stats[key]
        est, lo, hi = s["estimate"], s["ci95"][0], s["ci95"][1]
        x, xl, xh = (math.log2(v) for v in (est, lo, hi))
        colour = {"p": "orange!60", "c": "gray!45", "": "blue!30"}[kind]
        out.append(r"\node[anchor=east] at (%d.2,%d) {%s};" % (LO - 0, i, label.replace("%", r"\%")))
        out.append(r"\fill[%s] (0,%.2f) rectangle (%.4f,%.2f);" % (colour, i - 0.3, x, i + 0.3))
        out.append(r"\draw (%.4f,%d) -- (%.4f,%d); \draw (%.4f,%.2f) -- (%.4f,%.2f); \draw (%.4f,%.2f) -- (%.4f,%.2f);"
                   % (xl, i, xh, i, xl, i - 0.15, xl, i + 0.15, xh, i - 0.15, xh, i + 0.15))
        out.append(r"\node[anchor=west,font=\sffamily\scriptsize] at (%d.4,%d) {%s [%s, %s]};"
                   % (HI, i, fmt(est), fmt(lo), fmt(hi)))
    out += [r"\end{tikzpicture}", r"\end{document}", ""]
    (HERE / "result.tex").write_text("\n".join(out))
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "result.tex"], cwd=HERE,
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["pdftoppm", "-png", "-r", "130", "-singlefile", "result.pdf", "result"], cwd=HERE, check=True)
    for ext in (".aux", ".log"):
        (HERE / ("result" + ext)).unlink(missing_ok=True)
    print("result figure written")


if __name__ == "__main__":
    main()

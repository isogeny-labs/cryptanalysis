#!/usr/bin/env python3
"""Write figures/result.tex from a run's result.json and render it to PDF and PNG.

Usage: python3 make_figures.py run_github_<id>/panel/result.json

Ratios with 95% bootstrap intervals on a log2 axis; the dashed line is parity.
The primary is orange, controls grey. Every number is read from result.json.
Points are the 20 cold points; rank rows resample each arm's blocks, then its attempts within a block.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
ROWS = [
    ("PRIMARY end-to-end cold kP+cP / kM38+cM38", ("primary_e2e_kP_cP_over_kM38_cM38",), "p"),
    ("secondary e2e kP+cP / kM10+cM10", ("secondary_e2e_kP_cP_over_kM10_cM10",), ""),
    ("secondary e2e kM10+cM10 / kM38+cM38", ("secondary_e2e_kM10_cM10_over_kM38_cM38",), ""),
    ("probe law kP (probes per relation / law)", ("probe_law", "kP"), ""),
    ("probe law kM38 (gate band 0.80-1.20)", ("probe_law", "kM38"), ""),
    ("probe law kM10 (gate band 0.85-1.15)", ("probe_law", "kM10"), ""),
    ("cold without rank cP / cM38", ("cold_without_rank_cP_over_cM38",), ""),
    ("cold without rank cP / cM10", ("cold_without_rank_cP_over_cM10",), ""),
    ("online cP / cM38", ("online_cP_over_cM38",), ""),
    ("A/A e2e kM38+cM38 / kM38aa+cM38aa", ("aa_e2e_kM38_cM38_over_kM38aa_cM38aa",), "c"),
    ("A/A cold cM38 / cM38aa", ("aa_cold_cM38_over_cM38aa",), "c"),
    ("A/A rank per attempt kM38 / kM38aa", ("rank_attempt_kM38_over_kM38aa",), "c"),
    ("planted rank per attempt kM38X / kM38", ("planted_rank_attempt_kM38X_over_kM38",), "c"),
    ("e2e cold gap kP+cP / tuned rho", ("e2e_cold_gap_kP_cP_over_rT",), ""),
    ("e2e cold gap kM38+cM38 / tuned rho", ("e2e_cold_gap_kM38_cM38_over_rT",), ""),
    ("e2e cold gap kM10+cM10 / tuned rho", ("e2e_cold_gap_kM10_cM10_over_rT",), ""),
]


def get(stats, path):
    node = stats
    for key in path:
        node = node[key]
    return node


def main():
    path = Path(sys.argv[1]).resolve()
    res = json.loads(path.read_text())
    s = res["statistics"]
    x = lambda v: math.log(max(v, 1e-9), 2)  # noqa: E731
    lo_axis, hi_axis, n = 0.5, 512.0, len(ROWS)
    L = ["% Editable source for result.pdf, written by make_figures.py from " + str(path.relative_to(HERE)),
         "\\documentclass[tikz,border=6pt]{standalone}", "\\usepackage[T1]{fontenc}", "\\begin{document}",
         "\\begin{tikzpicture}[font=\\sffamily\\footnotesize,x=9mm,y=-5.6mm]"]
    for v in (0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512):
        L.append("\\draw[gray!35] (%.4f,-0.6) -- (%.4f,%d); \\node[gray] at (%.4f,%.1f) {%g};" % (x(v), x(v), n, x(v), n + 0.5, v))
    L.append("\\draw[red!70!black,dashed] (0,-0.6) -- (0,%d);" % n)
    L.append("\\node at (0,%.1f) {ratio (log scale); bars: estimate; whiskers: 95\\%% bootstrap (20 points; rank rows: blocks, then attempts)};" % (n + 1.3))
    L.append("\\node[anchor=west,font=\\sffamily\\bfseries] at (-13.5,-1.5) {Primary verdict: %s};" % res["decision"])
    for i, (label, key, kind) in enumerate(ROWS):
        st = get(s, key)
        est, (lo, hi) = st["estimate"], st["ci95"]
        col = {"p": "orange!60", "c": "gray!45"}.get(kind, "blue!30")
        L.append("\\node[anchor=east] at (%.4f,%d) {%s};" % (x(lo_axis) - 0.1, i, label))
        L.append("\\fill[%s] (0,%f) rectangle (%.4f,%f);" % (col, i - 0.3, x(est), i + 0.3))
        L.append("\\draw (%.4f,%d) -- (%.4f,%d); \\draw (%.4f,%f) -- (%.4f,%f); \\draw (%.4f,%f) -- (%.4f,%f);"
                 % (x(lo), i, x(hi), i, x(lo), i - 0.15, x(lo), i + 0.15, x(hi), i - 0.15, x(hi), i + 0.15))
        L.append("\\node[anchor=west,font=\\sffamily\\scriptsize] at (%.4f,%d) {%.4f [%.4f, %.4f]};" % (x(hi_axis) + 0.1, i, est, lo, hi))
    L += ["\\end{tikzpicture}", "\\end{document}", ""]
    FIG.mkdir(exist_ok=True)
    (FIG / "result.tex").write_text("\n".join(L))
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "result.tex"], cwd=FIG, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["pdftoppm", "-png", "-r", "150", "-singlefile", "result.pdf", "result"], cwd=FIG, check=True)
    for suffix in (".aux", ".log"):
        (FIG / ("result" + suffix)).unlink(missing_ok=True)
    print("figures written to " + str(FIG))


if __name__ == "__main__":
    main()

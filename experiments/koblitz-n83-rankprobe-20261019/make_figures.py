#!/usr/bin/env python3
"""Write figures/result.tex from a run's result.json and render it to PDF and PNG.

Usage: python3 make_figures.py run_github_<id>/panel/result.json

Ratios with 95% bootstrap intervals on a log2 axis; the dashed line is parity.
The primary is orange, controls grey. Every number is read from result.json.
Points are the 20 cold points; rank rows resample the blocks, then 600 attempts per block paired across arms.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
ROWS = [
    ("PRIMARY end-to-end cold kR+cR / kP+cP", ("primary_e2e_kR_cR_over_kP_cP",), "p"),
    ("rank per attempt kR / kP", ("rank_attempt_kR_over_kP",), ""),
    ("rank per attempt kR / kP, short third", ("rank_attempt_kR_over_kP_short_tercile",), ""),
    ("rank per attempt kR / kP, middle third", ("rank_attempt_kR_over_kP_middle_tercile",), ""),
    ("rank per attempt kR / kP, long third", ("rank_attempt_kR_over_kP_long_tercile",), ""),
    ("cold without rank cR / cP (same code)", ("cold_without_rank_cR_over_cP",), ""),
    ("online cR / cP (same code)", ("online_cR_over_cP",), ""),
    ("secondary e2e kR+cR / kP+cPI (+ lift build)", ("secondary_e2e_kR_cR_over_kP_cPI",), ""),
    ("cold without rank cP / cPI (lift build)", ("cold_without_rank_cP_over_cPI",), ""),
    ("A/A e2e kP+cP / kPaa+cR", ("aa_e2e_kP_cP_over_kPaa_cR",), "c"),
    ("A/A cold cP / cR", ("aa_cold_cP_over_cR",), "c"),
    ("A/A rank per attempt kP / kPaa", ("rank_attempt_kP_over_kPaa",), "c"),
    ("planted rank per attempt kPX / kP", ("planted_rank_attempt_kPX_over_kP",), "c"),
    ("e2e cold gap kR+cR / tuned rho", ("e2e_cold_gap_kR_cR_over_rT",), ""),
    ("e2e cold gap kP+cP / tuned rho", ("e2e_cold_gap_kP_cP_over_rT",), ""),
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
    L.append("\\node at (0,%.1f) {ratio (log scale); bars: estimate; whiskers: 95\\%% bootstrap (20 points; rank rows: blocks x 600 paired attempts)};" % (n + 1.3))
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

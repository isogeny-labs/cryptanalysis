#!/usr/bin/env python3
"""Write figures/result.tex from a run's result.json and render it to PDF and PNG.

Usage: python3 make_figures.py run_github_<id>/panel/result.json

Ratios with 95% bootstrap intervals on a log2 axis; the dashed line is parity.
The primary is orange, controls grey. Every number is read from result.json.
Rows resample the 64 points, paired across arms; the end-to-end row also resamples the shared rank process's 600 attempts.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
ROWS = [
    ("PRIMARY online cS / cF (S3 loop / frame loop)", ("primary_online_cS_over_cF",), "p"),
    ("online cS / cF, geometric mean", ("online_cS_over_cF_geometric",), ""),
    ("online cS / cF, short third", ("online_cS_over_cF_short_tercile",), ""),
    ("online cS / cF, middle third", ("online_cS_over_cF_middle_tercile",), ""),
    ("online cS / cF, long third", ("online_cS_over_cF_long_tercile",), ""),
    ("online cS / cFaa", ("online_cS_over_cFaa",), ""),
    ("secondary end-to-end cold cS / cF (shared K)", ("secondary_e2e_cS_over_cF",), ""),
    ("cold cS / cF", ("cold_cS_over_cF",), ""),
    ("setup cS / cF (same code)", ("setup_cS_over_cF",), ""),
    ("A/A online cF / cFaa", ("aa_online_cF_over_cFaa",), "c"),
    ("A/A cold cF / cFaa", ("aa_cold_cF_over_cFaa",), "c"),
    ("planted online cFX / cF", ("planted_online_cFX_over_cF",), "c"),
    ("online gap cS / tuned rho", ("online_gap_cS_over_rT",), ""),
    ("online gap cF / tuned rho", ("online_gap_cF_over_rT",), ""),
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
    lo_axis, hi_axis, n = 1 / 16, 4.0, len(ROWS)
    L = ["% Editable source for result.pdf, written by make_figures.py from " + str(path.relative_to(HERE)),
         "\\documentclass[tikz,border=6pt]{standalone}", "\\usepackage[T1]{fontenc}", "\\begin{document}",
         "\\begin{tikzpicture}[font=\\sffamily\\footnotesize,x=9mm,y=-5.6mm]"]
    for v in (1 / 16, 1 / 8, 0.25, 0.5, 1, 2, 4):
        L.append("\\draw[gray!35] (%.4f,-0.6) -- (%.4f,%d); \\node[gray] at (%.4f,%.1f) {%s};" % (x(v), x(v), n, x(v), n + 0.5, ("%g" % v) if v >= 1 else "1/%d" % round(1 / v)))
    L.append("\\draw[red!70!black,dashed] (0,-0.6) -- (0,%d);" % n)
    L.append("\\node at (0,%.1f) {ratio (log scale); bars: estimate; whiskers: 95\\%% bootstrap (64 points, paired)};" % (n + 1.3))
    L.append("\\node[anchor=west,font=\\sffamily\\bfseries] at (-9.5,-1.5) {Primary verdict: %s};" % res["decision"])
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

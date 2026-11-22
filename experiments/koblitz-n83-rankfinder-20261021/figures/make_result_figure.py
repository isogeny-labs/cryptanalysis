#!/usr/bin/env python3
"""Write figures/result.tex from a run's result.json and render it to PDF, SVG and PNG.

Usage: python3 figures/make_result_figure.py run_github_<id>/panel/result.json

Ratios with 95% bootstrap intervals on a log2 axis; the dashed line is parity.
The primary is orange, controls grey. Every number is read from result.json.
Points are the 12 points; pair rows resample points, then pairs within a
point; probe-law rows resample blocks, then attempts; planted rows resample pairs.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
FIG = HERE / "figures"
ROWS = [
    ("PRIMARY end-to-end cold A / B (36 pairs)", ("primary_e2e_paired_A_over_B",), "p"),
    ("rank stage kM38IC / kM38RF (stage secondary)", ("rank_stage_secondary_A_over_B",), ""),
    ("setup A / B", ("setup_A_over_B",), ""),
    ("cold (setup + online) A / B", ("cold_A_over_B",), ""),
    ("index build, cold processes A / B", ("index_build_A_over_B",), ""),
    ("self-test (scan) A / B", ("scan_selftest_A_over_B",), ""),
    ("online A / B", ("online_A_over_B",), ""),
    ("process CPU time A / B", ("cpu_time_A_over_B",), ""),
    ("probe law kM38IC, side A (gate band 0.80-1.20)", ("probe_law", "kM38IC"), ""),
    ("probe law kM38RF, side B (probes per relation / law)", ("probe_law", "kM38RF"), ""),
    ("A/A e2e B / Baa (control, 0.97-1.03)", ("aa_e2e_B_over_Baa",), "c"),
    ("A/A cold B / Baa (control, 0.97-1.03)", ("aa_cold_B_over_Baa",), "c"),
    ("planted rank stage kM38RFX / kM38RF (control)", ("planted_rank_stage_kM38RFX_over_kM38RF",), "c"),
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
    lo_axis, hi_axis, n = 0.5, 4.0, len(ROWS)
    L = ["% Editable source for result.pdf, written by make_result_figure.py from " + str(path.relative_to(HERE)),
         "\\documentclass[tikz,border=6pt]{standalone}", "\\usepackage[T1]{fontenc}", "\\begin{document}",
         "\\begin{tikzpicture}[font=\\sffamily\\footnotesize,x=9mm,y=-5.6mm]"]
    for v in (0.5, 1, 2, 4):
        L.append("\\draw[gray!35] (%.4f,-0.6) -- (%.4f,%d); \\node[gray] at (%.4f,%.1f) {%g};" % (x(v), x(v), n, x(v), n + 0.5, v))
    L.append("\\draw[red!70!black,dashed] (0,-0.6) -- (0,%d);" % n)
    L.append("\\node at (0,%.1f) {ratio (log scale); bars: estimate; whiskers: 95\\%% bootstrap};" % (n + 1.3))
    L.append("\\node[anchor=west,font=\\sffamily\\bfseries] at (-9,-1.5) {Primary verdict: %s};" % res["decision"])
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
    subprocess.run(["pdftocairo", "-svg", "result.pdf", "result.svg"], cwd=FIG, check=True)
    for suffix in (".aux", ".log"):
        (FIG / ("result" + suffix)).unlink(missing_ok=True)
    print("figures written to " + str(FIG))


if __name__ == "__main__":
    main()

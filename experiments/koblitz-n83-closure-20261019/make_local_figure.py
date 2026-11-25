#!/usr/bin/env python3
"""Write figures/local_law.tex from inputs/local_decisive_test.json and render PDF and PNG.

The local decisive test's probe law: mean probes per relation over law
r / (166 E) per local rank block (dots; seeds 301..), and pooled over the
blocks with a 95% normal interval (bar), for M38 and M10, with the frozen
gate bands (shaded) and the baseline's measured 0.978 (run 39214027289, kP,
2,400 attempts; dashed). Local diagnostic on the cloud-agent VM, not timing
evidence.
"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
BANDS = {"M38": (0.80, 1.20), "M10": (0.85, 1.15)}


def main():
    rec = json.loads((HERE / "inputs" / "local_decisive_test.json").read_text())["bases"]
    x = lambda v: (v - 0.4) * 10.0  # noqa: E731  (0.4..1.6 -> 0..12 cm)
    L = ["% Editable source for local_law.pdf, written by make_local_figure.py from inputs/local_decisive_test.json",
         "\\documentclass[tikz,border=6pt]{standalone}", "\\usepackage[T1]{fontenc}", "\\begin{document}",
         "\\begin{tikzpicture}[font=\\sffamily\\footnotesize,x=1cm,y=-1cm]"]
    for v in (0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6):
        L.append("\\draw[gray!35] (%.3f,-0.4) -- (%.3f,3.6); \\node[gray] at (%.3f,3.9) {%.1f};" % (x(v), x(v), x(v), v))
    L.append("\\draw[red!70!black,dashed] (%.3f,-0.4) -- (%.3f,3.6);" % (x(0.978), x(0.978)))
    L.append("\\node[red!70!black,font=\\sffamily\\scriptsize,anchor=south] at (%.3f,-0.4) {K600 baseline 0.978};" % x(0.978))
    L.append("\\node at (6,4.5) {mean probes per relation / law $r/(166E)$ (local VM; dots: one rank block of K' attempts; bar: pooled, 95\\%)};")
    for row, name in enumerate(("M38", "M10")):
        y = 0.8 + 1.8 * row
        r = rec[name]
        lo, hi = BANDS[name]
        L.append("\\fill[green!10] (%.3f,%.2f) rectangle (%.3f,%.2f);" % (x(lo), y - 0.6, x(hi), y + 0.6))
        L.append("\\node[anchor=east] at (-0.2,%.2f) {%s: %d columns, %d attempts};" % (
            y, name, r["columns"], r["pooled_attempts"]))
        for b in r["blocks"]:
            L.append("\\fill[blue!60] (%.3f,%.2f) circle (1.3pt);" % (x(b["mean_probes_over_law"]), y - 0.3))
        m, se = r["pooled_mean_probes_over_law"], r["pooled_se"]
        L.append("\\draw[very thick,orange!80!black] (%.3f,%.2f) -- (%.3f,%.2f);" % (x(m - 1.96 * se), y + 0.2, x(m + 1.96 * se), y + 0.2))
        L.append("\\fill[orange!80!black] (%.3f,%.2f) circle (2pt);" % (x(m), y + 0.2))
        L.append("\\node[anchor=west,font=\\sffamily\\scriptsize] at (12.2,%.2f) {pooled %.3f $\\pm$ %.3f (1 s.e.); band %.2f--%.2f};" % (
            y, m, se, lo, hi))
    L += ["\\end{tikzpicture}", "\\end{document}", ""]
    FIG.mkdir(exist_ok=True)
    (FIG / "local_law.tex").write_text("\n".join(L))
    for stem in ("local_law", "design"):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", stem + ".tex"], cwd=FIG, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["pdftoppm", "-png", "-r", "150", "-singlefile", stem + ".pdf", stem], cwd=FIG, check=True)
        for suffix in (".aux", ".log"):
            (FIG / (stem + suffix)).unlink(missing_ok=True)
    print("figures written to " + str(FIG))


if __name__ == "__main__":
    main()

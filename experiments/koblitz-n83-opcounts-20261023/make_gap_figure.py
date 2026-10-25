#!/usr/bin/env python3
"""Draw each IC arm's gap to the matched rho (cost ratio arm / rT) against the GAE weight.

Reads the v2 analysis result (`opcounts_result-v2.json`, written by
`analyze_v2.py`) and writes `figures/<name>.tex` (pgfplots, log y axis, 95%
paired bootstrap intervals as error bars, the line ratio = 1 marking parity
with rho; solid = main band, dashed = the Frobenius-at-1-GAE sensitivity).
With pdflatex, pdftoppm and pdftocairo present it also writes the PDF, PNG and
SVG next to it. The rho's scalar-multiplication bound is drawn at its 0 GAE
end; the 104 GAE end is listed in the caption data and differs by < 0.1%.
"""

import argparse
import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
STYLES = {"S": "blue, mark=*", "P": "red!70!black, mark=square*"}


def series(band, arm):
    out = []
    for i, w in enumerate(band["weights_gae"]):
        cell = band["gap_to_reference"][arm]["%g" % w][0]
        assert cell["rho_scalar_mul_gae"] == 0
        lo, hi = cell["ci95"]
        r = cell["ratio"]
        out.append("(%d,%.6g) -= (0,%.6g) += (0,%.6g)" % (i, r, r - lo, hi - r))
    return " ".join(out)


def tex(result, title):
    band, sens = result["band"], result["band_frobenius_as_group"]
    weights = band["weights_gae"]
    lines = [r"\documentclass[tikz,border=4pt]{standalone}", r"\usepackage{pgfplots}",
             r"\pgfplotsset{compat=1.17}", r"\begin{document}", r"\begin{tikzpicture}",
             r"\begin{axis}[width=11cm, height=7cm, ymode=log, xmin=-0.3, xmax=%g," % (len(weights) - 0.7),
             r"  xlabel={weight $w$ (GAE per unpriced native operation)},",
             r"  ylabel={gap to matched rho: cost(arm) / cost(rT)}, xtick={%s}," %
             ",".join("%d" % i for i in range(len(weights))),
             r"  xticklabels={%s}, title={%s}, legend pos=outer north east, legend cell align=left]" %
             (",".join("%g" % w for w in weights), title),
             r"\addplot[gray, dotted, domain=-0.3:%g, samples=2, forget plot] {1};" % (len(weights) - 0.7)]
    for arm in ("S", "P"):
        for data, dash, label in ((band, "", arm), (sens, ", dashed", arm + r" (Frobenius at 1 GAE)")):
            lines.append(r"\addplot[%s%s, error bars/.cd, y dir=both, y explicit] coordinates {%s};" %
                         (STYLES[arm], dash, series(data, arm)))
            lines.append(r"\addlegendentry{%s}" % label)
    lines += [r"\node[anchor=south west, font=\footnotesize, gray] at (axis cs:-0.25,1) {parity with rho};",
              r"\end{axis}", r"\end{tikzpicture}", r"\end{document}"]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_json", type=Path)
    parser.add_argument("--name", default="band_gap")
    parser.add_argument("--title", default="Section 5a band")
    args = parser.parse_args()
    result = json.loads(args.result_json.read_text())
    out = HERE / "figures"
    out.mkdir(exist_ok=True)
    path = out / (args.name + ".tex")
    path.write_text(tex(result, args.title))
    if shutil.which("pdflatex") and shutil.which("pdftoppm"):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", path.name], cwd=out,
                       check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["pdftoppm", "-png", "-r", "160", "-singlefile", args.name + ".pdf", args.name], cwd=out,
                       check=True)
        if shutil.which("pdftocairo"):
            subprocess.run(["pdftocairo", "-svg", args.name + ".pdf", args.name + ".svg"], cwd=out, check=True)
        for suffix in (".aux", ".log"):
            (out / (args.name + suffix)).unlink(missing_ok=True)
    print(path)


if __name__ == "__main__":
    main()

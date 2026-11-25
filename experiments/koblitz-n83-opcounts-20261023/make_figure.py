#!/usr/bin/env python3
"""Draw the section 5a band (cost per solved target against the GAE weight) from a band.json.

Writes `figures/<name>.tex` (pgfplots, log y axis: one line per arm, the rho
drawn at both ends of its scalar-multiplication bound) and, when pdflatex and
pdftoppm are present, `<name>.pdf` and `<name>.png` next to it.
"""

import argparse
import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
STYLES = ["blue, mark=*", "red!70!black, mark=square*", "black, mark=triangle*", "green!50!black, mark=diamond*"]


def tex(result, title):
    weights = result["weights_gae"]
    lines = [r"\documentclass[tikz,border=4pt]{standalone}", r"\usepackage{pgfplots}",
             r"\pgfplotsset{compat=1.17}", r"\begin{document}", r"\begin{tikzpicture}",
             r"\begin{axis}[width=11cm, height=7cm, ymode=log, xlabel={weight $w$ (GAE per unpriced native operation)},",
             r"  ylabel={priced cost per solved target (GAE)}, xtick={%s}, legend pos=outer north east," %
             ",".join("%d" % i for i in range(len(weights))),
             r"  xticklabels={%s}, title={%s}, legend cell align=left]" % (",".join("%g" % w for w in weights), title)]
    for index, (name, arm) in enumerate(result["arms"].items()):
        style = STYLES[index % len(STYLES)]
        ends = len(next(iter(arm["cost_gae"].values())))
        for end in range(ends):
            values = [arm["cost_gae"]["%g" % w][end] for w in weights]
            if end and values == [arm["cost_gae"]["%g" % w][0] for w in weights]:
                continue
            coordinates = " ".join("(%d,%.6g)" % (i, max(v, 1e-9)) for i, v in enumerate(values))
            dash = ", dashed" if end else ""
            lines.append(r"\addplot[%s%s] coordinates {%s};" % (style, dash, coordinates))
            label = name if not end else name + r" (rho scalar mults at %g GAE)" % result["rho_scalar_mul_bound_gae"][end]
            lines.append(r"\addlegendentry{%s}" % label.replace("_", r"\_"))
    lines += [r"\end{axis}", r"\end{tikzpicture}", r"\end{document}"]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("band_json", type=Path)
    parser.add_argument("--name", default="band")
    parser.add_argument("--title", default="Section 5a band")
    args = parser.parse_args()
    result = json.loads(args.band_json.read_text())
    out = HERE / "figures"
    out.mkdir(exist_ok=True)
    path = out / (args.name + ".tex")
    path.write_text(tex(result, args.title))
    if shutil.which("pdflatex") and shutil.which("pdftoppm"):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", path.name], cwd=out,
                       check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["pdftoppm", "-png", "-r", "160", "-singlefile", args.name + ".pdf", args.name], cwd=out,
                       check=True)
        for suffix in (".aux", ".log"):
            (out / (args.name + suffix)).unlink(missing_ok=True)
    print(path)


if __name__ == "__main__":
    main()

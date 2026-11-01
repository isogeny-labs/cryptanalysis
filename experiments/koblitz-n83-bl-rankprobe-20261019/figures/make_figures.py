#!/usr/bin/env python3
"""Write `figures/power.dat` and `figures/power.tex` from `analysis/power.json`, then build them.

The figure plots, for each simulated panel size n, the median and the 90th
percentile of the 95% interval's width ratio (upper / lower) of the primary
G = mean cP online / mean BL online, at BL scale 1 (the frozen rule's line at
2.0 and the chosen n are marked), and the simulated median G at BL scales
0.5, 1 and 2. A sizing simulation from a model-based prior; not a result.
`design.tex` is drawn by hand and built by the same `pdflatex` call.
Requires pdflatex (pgfplots) and pdftoppm.
"""

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
POWER = json.loads((HERE.parent / "analysis" / "power.json").read_text())

TEX = r"""\documentclass[border=6pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{pgfplots}
\pgfplotsset{compat=1.17}
%% Sizing simulation of koblitz-n83-bl-rankprobe-20261019 (analysis/power.json). Not a result.
\begin{document}
\begin{tikzpicture}[font=\sffamily\small]
\begin{axis}[name=w, width=8cm, height=6cm, xlabel={points in the cold panel, $n$},
  ylabel={95\%% interval of $G$: upper / lower}, xtick={20,32,48,64,80,96}, ymin=1, ymax=4.5,
  legend style={font=\scriptsize, at={(0.98,0.98)}, anchor=north east},
  title={\small precision of the primary (400 simulations per $n$)}]
\addplot[thick, blue, mark=*] table[x=n, y=median] {power.dat};
\addlegendentry{median}
\addplot[thick, blue!50, dashed, mark=o] table[x=n, y=p90] {power.dat};
\addlegendentry{90th percentile}
\addplot[red, densely dotted, domain=16:100] {%(target)s};
\addlegendentry{frozen rule: median $\le$ %(target)s}
\addplot[red, thick, forget plot] coordinates {(%(chosen)d,1) (%(chosen)d,4.5)};
\node[red, right, font=\scriptsize] at (axis cs:%(chosen)d,1.3) {chosen $n=%(chosen)d$};
\end{axis}
\begin{axis}[at={(w.east)}, anchor=west, xshift=1.6cm, width=8cm, height=6cm, xlabel={points in the cold panel, $n$},
  ylabel={simulated median $G$ (IC online / BL online)}, xtick={20,32,48,64,80,96}, ymode=log, ytick={5,10,20,40}, yticklabels={5,10,20,40}, ymin=5, ymax=60,
  legend style={font=\scriptsize, at={(0.98,0.98)}, anchor=north east},
  title={\small the prior's $G$ at three BL step scales}]
\addplot[thick, black!60, mark=square*] table[x=n, y=g05] {power.dat};
\addlegendentry{BL steps $\times 0.5$}
\addplot[thick, black, mark=*] table[x=n, y=g1] {power.dat};
\addlegendentry{model scale}
\addplot[thick, black!40, mark=triangle*] table[x=n, y=g2] {power.dat};
\addlegendentry{BL steps $\times 2$}
\end{axis}
\end{tikzpicture}
\end{document}
"""


def main():
    cells = {k: {c["n"]: c for c in v} for k, v in POWER["cells"].items()}
    lines = ["n median p90 g05 g1 g2"]
    for n in POWER["grid"]:
        one = cells["bl_scale_1.0"][n]
        lines.append("%d %.4f %.4f %.3f %.3f %.3f" % (n, one["median_width_ratio"], one["p90_width_ratio"],
                                                      cells["bl_scale_0.5"][n]["median_estimate"],
                                                      one["median_estimate"],
                                                      cells["bl_scale_2.0"][n]["median_estimate"]))
    (HERE / "power.dat").write_text("\n".join(lines) + "\n")
    (HERE / "power.tex").write_text(TEX % {"target": "2.0", "chosen": POWER["chosen_points"]})
    for name in ("design", "power"):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", name + ".tex"], cwd=HERE,
                       check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["pdftoppm", "-png", "-r", "130", "-singlefile", name + ".pdf", name], cwd=HERE, check=True)
        for ext in (".aux", ".log"):
            (HERE / (name + ext)).unlink(missing_ok=True)
    print("figures written")


if __name__ == "__main__":
    main()

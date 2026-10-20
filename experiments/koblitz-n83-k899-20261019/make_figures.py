#!/usr/bin/env python3
"""Write the figures' pgfplots sources and render them to PDF and PNG.

Usage:
  python3 make_figures.py design                      # figures/design.tex from protocol.json + inputs/k899_identity.json
  python3 make_figures.py result run_github_<id>/panel/result.json   # figures/result.tex

design: the pre-registration cost model E2E(K) = 146.9/a + 21.6 a^2 + 0.31 a + 0.38/a^2 s (a = K/600; a
model, not a result), the archived K600 baseline (166.0 s, run 39214027289), the diagnostic's single-process
end-to-end cost (rank stage + cold, one rank seed, Q0) at K600 and K899, and the 2^27-slot cliff between K899
and K900. result: ratios with 95% bootstrap intervals on a log2 axis, primary orange, controls grey; every
number read from result.json.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
PRE = r"""\documentclass[border=4pt]{standalone}
\usepackage{pgfplots}
\pgfplotsset{compat=1.17}
\begin{document}
"""


def render(name, body):
    FIG.mkdir(exist_ok=True)
    tex = FIG / (name + ".tex")
    tex.write_text(PRE + body + "\\end{document}\n")
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex.name], cwd=FIG, check=True,
                   stdout=subprocess.DEVNULL)
    subprocess.run(["pdftoppm", "-png", "-r", "160", "-singlefile", name + ".pdf", name], cwd=FIG, check=True)
    for ext in (".aux", ".log"):
        (FIG / (name + ext)).unlink(missing_ok=True)
    print(FIG / (name + ".pdf"))


def model(k):
    a = k / 600
    return 146.9 / a + 21.6 * a * a + 0.31 * a + 0.38 / (a * a)


def design():
    ident = json.loads((HERE / "inputs" / "k899_identity.json").read_text())
    d = ident["diagnostic"]
    base = model(600)
    curve = " ".join("(%d,%.4f)" % (k, model(k) / base) for k in range(400, 1201, 20))
    e600 = d["rank_stage_ms"]["K600"] + d["cold_ms"]["K600"]
    e899 = d["rank_stage_ms"]["K899"] + d["cold_ms"]["K899"]
    body = r"""\begin{tikzpicture}
\begin{axis}[width=12cm,height=7.5cm,xlabel={factor-base size $K$ (orbit columns)},
 ylabel={E2E cold / E2E cold at $K=600$},xmin=380,xmax=1220,ymin=0.8,ymax=1.3,grid=major,
 legend style={font=\footnotesize,at={(0.5,-0.2)},anchor=north,cells={anchor=west}},
 title={\footnotesize n=83 a=1 rank-probe producer: relative cost model and the go/no-go diagnostic}]
\addplot[blue,thick] coordinates {%s};
\addlegendentry{cost model $E(K)/E(600)$, $E = 146.9/a + 21.6a^2 + 0.31a + 0.38/a^2$ s, $a=K/600$ (model)}
\addplot[only marks,mark=*,mark size=2.8pt,orange] coordinates {(600,1) (899,%.4f)};
\addlegendentry{diagnostic, %s (run 39292460576): rank stage + cold, one process each, one seed}
\draw[dashed,red] (axis cs:899.5,0.8) -- (axis cs:899.5,1.3);
\node[red,font=\scriptsize,anchor=west,align=left] at (axis cs:910,1.12) {K900: root table\\$2^{27}\to2^{28}$ slots\\(2 GiB $\to$ 4 GiB)};
\node[orange!70!black,font=\scriptsize,anchor=north] at (axis cs:899,%.4f) {%.3f};
\node[blue,font=\scriptsize,anchor=north] at (axis cs:960,%.4f) {model %.3f};
\end{axis}
\end{tikzpicture}
""" % (curve, e899 / e600, d["where"], e899 / e600 - 0.01, e899 / e600, model(899) / base - 0.01,
       model(899) / base)
    render("design", body)


ROWS = [
    ("PRIMARY e2e cold kP600+cP600 / kP899+cP899", "primary_e2e_kP600_cP600_over_kP899_cP899", "p"),
    ("rank stage kP600 / kP899", "rank_stage_kP600_over_kP899", ""),
    ("cold without rank cP899 / cP600", "cold_without_rank_cP899_over_cP600", ""),
    ("index build cP899 / cP600", "index_build_cP899_over_cP600", ""),
    ("online cP899 / cP600", "online_cP899_over_cP600", ""),
    ("secondary e2e kP600+cPI600 / kP899+cPI899", "secondary_e2e_kP600_cPI600_over_kP899_cPI899", ""),
    ("secondary e2e kP600+cP600 / kP899+cPI899", "secondary_e2e_kP600_cP600_over_kP899_cPI899", ""),
    ("A/A e2e kP899+cP899 / kP899aa+cP899aa", "aa_e2e_kP899_cP899_over_kP899aa_cP899aa", "c"),
    ("A/A cold cP899 / cP899aa", "aa_cold_cP899_over_cP899aa", "c"),
    ("A/A rank per attempt kP899 / kP899aa", "rank_attempt_kP899_over_kP899aa", "c"),
    ("planted rank per attempt kPX899 / kP899", "planted_rank_attempt_kPX899_over_kP899", "c"),
]


def result(path):
    stats = json.loads(Path(path).read_text())["statistics"]
    rows = [(label, stats.get(key), kind) for label, key, kind in ROWS if stats.get(key)]
    n = len(rows)
    lines = []
    for i, (label, e, kind) in enumerate(rows):
        y = n - i
        color = "orange" if kind == "p" else "gray" if kind == "c" else "blue"
        lo, hi = e["ci95"]
        lines.append(r"\addplot[%s,thick,mark=*,error bars/.cd,x dir=both,x explicit] coordinates {(%.5f,%d) +- (0,0) -= (%.5f,0) += (%.5f,0)};"
                     % (color, math.log2(e["estimate"]), y, math.log2(e["estimate"]) - math.log2(lo),
                        math.log2(hi) - math.log2(e["estimate"])))
    ticks = ",".join(str(n - i) for i in range(n))
    labels = ",".join("{%s}" % r[0].replace("_", r"\_") for r in rows)
    body = r"""\begin{tikzpicture}
\begin{axis}[width=11cm,height=%.1fcm,xlabel={ratio (log$_2$ scale; 0 = parity)},ytick={%s},yticklabels={%s},
 yticklabel style={font=\scriptsize},ymin=0.3,ymax=%.1f,grid=major]
%s
\draw[dashed] (axis cs:0,0.3) -- (axis cs:0,%.1f);
\end{axis}
\end{tikzpicture}
""" % (0.8 * n + 2, ticks, labels, n + 0.7, "\n".join(lines), n + 0.7)
    render("result", body)


if __name__ == "__main__":
    if sys.argv[1] == "design":
        design()
    else:
        result(sys.argv[2])

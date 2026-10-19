#!/usr/bin/env python3
"""Setup profile of the archived cold processes, and its figure (before any timing here).

Reads run 39214027289's receipt (`--archive`, a directory holding `runs.jsonl`
and `runs/`; default the rank-probe experiment's archived panel) and writes
`inputs/setup_profile_archived.json`: per cold arm (cP, the selected index
canonicalizer; cPI, lift_scan) the median over its 20 cold points of each
cold phase the producer reports (`cold_phase_ms`), with the Feistel scan
self-test split out of `setup_input_control`. Then writes
`figures/profile.tex` and renders it to PDF and PNG. Tier 1 timings from that
run, used only to choose this experiment's arms; no timing of this
experiment enters it. `--figure-only` re-renders from the JSON.
"""
import argparse
import base64
import json
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent / "koblitz-n83-rankprobe-20261019" / "run_github_39214027289" / "panel"
OUT = HERE / "inputs" / "setup_profile_archived.json"
FIG = HERE / "figures"
PHASES = [("base load", "factor_base", "gray!45"),
          ("normal basis + self-test", "precompute_basis_and_selftest", "gray!70"),
          ("index build", "precompute_index", "orange!60"),
          ("factor-log load + verify", "relation_la", "yellow!70"),
          ("Feistel scan self-test", "scan_order_selftest", "red!55"),
          ("other input control", "other_input_control", "cyan!50"),
          ("one-target online", "online", "blue!45")]


def build(panel):
    per_arm = {"cP": {}, "cPI": {}}
    for line in (panel / "runs.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["arm"] not in per_arm or not row["segment"].startswith("C") or row["status"] != "valid":
            continue
        text = (panel / row["stdout_file"]).read_text()
        raw = json.loads(base64.b64decode([l[8:] for l in text.splitlines() if l.startswith("raw_b64=")][0]))
        summary = next(r for r in raw["records"] if r.get("kind") == "compact_orbit_dlp_summary")
        phases = summary["cold_phase_ms"]
        selftest = summary["scan_order_selftest"]["ms"]
        values = {"factor_base": phases["factor_base"],
                  "precompute_basis_and_selftest": phases["precompute_basis_and_selftest"],
                  "precompute_index": phases["precompute_index"], "relation_la": phases["relation_la"],
                  "scan_order_selftest": selftest,
                  "other_input_control": phases["setup_input_control"] - selftest,
                  "online": sum(v for k, v in phases.items() if k.startswith("target_")),
                  "cold_in_process_ms": summary["cold_in_process_ms"]}
        for key, value in values.items():
            per_arm[row["arm"]].setdefault(key, []).append(value)
    return {"schema": 1, "source": "koblitz-n83-rankprobe-20261019/run_github_39214027289, arms cP and cPI, cold points",
            "statistic": "median over the cold points, ms",
            "points": {arm: len(v["online"]) for arm, v in per_arm.items()},
            "median_ms": {arm: {k: statistics.median(v) for k, v in vals.items()} for arm, vals in per_arm.items()}}


def figure(profile):
    scale = 0.55  # mm per 100 ms
    rows = [("cP (selected index canonicalizer)", "cP"), ("cPI (lift\\_scan index build)", "cPI")]
    L = ["% Editable source for profile.pdf, written by make_setup_profile.py from inputs/setup_profile_archived.json",
         "\\documentclass[tikz,border=6pt]{standalone}", "\\usepackage[T1]{fontenc}", "\\begin{document}",
         "\\begin{tikzpicture}[font=\\sffamily\\footnotesize]"]
    for i, (label, arm) in enumerate(rows):
        y = -i * 1.1
        x = 0.0
        med = profile["median_ms"][arm]
        L.append("\\node[anchor=east] at (-0.1,%.2f) {%s};" % (y, label))
        for name, key, colour in PHASES:
            w = med[key] / 100 * scale / 10
            L.append("\\fill[%s,draw=white] (%.4f,%.2f) rectangle (%.4f,%.2f);" % (colour, x, y - 0.35, x + w, y + 0.35))
            if w > 0.6:
                L.append("\\node[font=\\sffamily\\scriptsize] at (%.4f,%.2f) {%.0f};" % (x + w / 2, y, med[key]))
            x += w
        L.append("\\node[anchor=west] at (%.4f,%.2f) {%.1f s};" % (x + 0.1, y, med["cold_in_process_ms"] / 1000))
    for s in range(0, 25, 5):
        xs = s * 1000 / 100 * scale / 10
        L.append("\\draw[gray] (%.4f,-1.6) -- (%.4f,-1.7) node[below] {%d s};" % (xs, xs, s))
    for j, (name, key, colour) in enumerate(PHASES):
        L.append("\\fill[%s] (%.2f,-2.5) rectangle ++(0.25,0.25); \\node[anchor=west,font=\\sffamily\\scriptsize] at (%.2f,-2.38) {%s};"
                 % (colour, (j % 4) * 3.3, (j % 4) * 3.3 + 0.3, name) if j < 4 else
                 "\\fill[%s] (%.2f,-3.0) rectangle ++(0.25,0.25); \\node[anchor=west,font=\\sffamily\\scriptsize] at (%.2f,-2.88) {%s};"
                 % (colour, (j % 4) * 3.3, (j % 4) * 3.3 + 0.3, name))
    L.append("\\node[anchor=west,font=\\sffamily\\scriptsize] at (0,-3.5) {Median cold phase (ms) over 20 points, run 39214027289 (Tier 1, one pinned CPU); archived, not this experiment's timing.};")
    L += ["\\end{tikzpicture}", "\\end{document}", ""]
    FIG.mkdir(exist_ok=True)
    (FIG / "profile.tex").write_text("\n".join(L))
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "profile.tex"], cwd=FIG, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["pdftoppm", "-png", "-r", "160", "-singlefile", "profile.pdf", "profile"], cwd=FIG, check=True)
    for suffix in (".aux", ".log"):
        (FIG / ("profile" + suffix)).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    parser.add_argument("--figure-only", action="store_true")
    args = parser.parse_args()
    if not args.figure_only:
        OUT.write_text(json.dumps(build(args.archive), indent=1, sort_keys=True) + "\n")
    figure(json.loads(OUT.read_text()))
    print(str(OUT))


if __name__ == "__main__":
    main()

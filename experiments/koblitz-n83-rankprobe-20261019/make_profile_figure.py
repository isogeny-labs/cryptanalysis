#!/usr/bin/env python3
"""Write figures/profile.tex from smoke/profile_local.json and render it to PDF and PNG.

LOCAL DIAGNOSTIC (cloud-agent VM): median ns per probe of each stage of the rank
probe, the rank-cut loop (kR) against the frame loop (kP), over 15 interleaved
rounds of 6,000 states (default build). Stacked bars, one segment per stage; the
segment widths are the median increments of the cumulative profile, so they
sum to the cumulative total of the last stage. Not timing evidence.
"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
STAGES = [("fold rebuild", "fold_rebuild", "fold_rebuild", "gray!40"),
          ("root (x, y)", "plus_root_y", "plus_root_xy", "gray!70"),
          ("per-candidate input maps + prefix products", "plus_inputs_maps_and_prefix_products",
           "plus_prefix_products", "red!55"),
          ("batched inversion", "plus_batched_inversion", "plus_batched_inversion", "orange!60"),
          ("lambda products, normal-basis maps, partners", "plus_lambda_maps_and_partners",
           "plus_lambda_maps_and_partners", "yellow!70"),
          ("lift\\_scan keys (both partners)", "plus_lift_scan_keys", "plus_lift_scan_keys", "green!50"),
          ("prefetch + key store", "plus_prefetch_and_key_store", "plus_prefetch_and_key_store", "cyan!50"),
          ("lookups + hit check", "plus_lookups", "plus_lookups", "blue!45")]


def main():
    run = json.loads((HERE / "smoke" / "profile_local.json").read_text())["runs"]["prof_bin"]
    rc = run["median_increment_ns_per_probe_rankcut_loop"]
    fr = run["median_increment_ns_per_probe_frame_loop"]
    prod = run["median_production_ns_per_probe"]
    scale = 0.05  # cm per ns
    L = ["% Editable source for profile.pdf, written by make_profile_figure.py from smoke/profile_local.json",
         "\\documentclass[tikz,border=6pt]{standalone}", "\\usepackage[T1]{fontenc}", "\\begin{document}",
         "\\begin{tikzpicture}[font=\\sffamily\\footnotesize]"]
    for row, (name, inc) in enumerate((("rank-cut loop (kR)", rc), ("frame loop (kP)", fr))):
        y = -row * 1.2
        x = 0.0
        for label, krc, kfr, color in STAGES:
            w = max(inc[krc if row == 0 else kfr], 0.0) * scale
            L.append("\\fill[%s] (%.3f,%.2f) rectangle (%.3f,%.2f);" % (color, x, y - 0.4, x + w, y + 0.4))
            L.append("\\draw[white] (%.3f,%.2f) -- (%.3f,%.2f);" % (x + w, y - 0.4, x + w, y + 0.4))
            x += w
        L.append("\\node[anchor=east] at (-0.1,%.2f) {%s};" % (y, name))
        L.append("\\node[anchor=west] at (%.3f,%.2f) {%.0f ns (production loop %.0f)};"
                 % (x + 0.1, y, x / scale, prod["padd" if row == 0 else "frame"]))
    for v in range(0, 301, 50):
        L.append("\\draw[gray!50] (%.2f,-1.75) -- (%.2f,-1.85) node[below,gray] {%d};" % (v * scale, v * scale, v))
    L.append("\\node at (%.2f,-2.45) {median ns per probe (cumulative stages; 15 rounds x 6,000 states; LOCAL VM DIAGNOSTIC, not timing evidence)};" % (150 * scale))
    for i, (label, _, _, color) in enumerate(STAGES):
        cx, cy = (i // 4) * 7.5, 2.75 - 0.42 * (i % 4)
        L.append("\\fill[%s] (%.2f,%.2f) rectangle (%.2f,%.2f); \\node[anchor=west,font=\\sffamily\\scriptsize] at (%.2f,%.2f) {%s};"
                 % (color, cx, cy - 0.15, cx + 0.3, cy + 0.15, cx + 0.35, cy, label))
    L += ["\\end{tikzpicture}", "\\end{document}", ""]
    (FIG / "profile.tex").write_text("\n".join(L))
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "profile.tex"], cwd=FIG, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["pdftoppm", "-png", "-r", "150", "-singlefile", "profile.pdf", "profile"], cwd=FIG, check=True)
    for suffix in (".aux", ".log"):
        (FIG / ("profile" + suffix)).unlink(missing_ok=True)
    print("figures/profile.* written")


if __name__ == "__main__":
    main()

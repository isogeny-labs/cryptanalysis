# glv-cap-by-size-walltime-20261107

Tier 1 wall time of #1341's size-dependent GLV table cap (128 from 40 bits, else 32) against main,
j = 1728 and j = 0 at 38 (null), 40, 41, 42, 44, 46 and 48 bits. Read `PROTOCOL.md` first; it was frozen
before any timing and `sha256sum -c PROTOCOL.sha256` checks it.

| file | role |
|---|---|
| `PROTOCOL.md` | question, arms, workload, claim rule, predictions |
| `bench_glv_panel.c` | the timed program |
| `make_panel.py` | builds the panels and manifests (seed 20261107) |
| `panel_<family>_<bits>.txt`, `manifest_<family>_<bits>.json` | frozen panels and Tier 1 manifests |
| `gh_manifest.py` | rewrites a frozen manifest for the GitHub runner |
| `analyze.py`, `chart.py` | results.json and the SVG chart from the workflow artifact |
| `../../.github/workflows/glv-cap-by-size-tier1.yml` | builds the arms from pinned commits and runs `scripts/isolated_bench.py` |

This README was added after the freeze, in the commit that starts the workflow; it changes no frozen file.
Results follow in later commits.

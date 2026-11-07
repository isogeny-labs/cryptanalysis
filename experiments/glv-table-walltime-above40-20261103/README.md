# glv-table-walltime-above40-20261103

Tier 1 wall time of a 128-entry GLV r-adding table (#1335) against main's 32 entries, j = 1728 and
j = 0 at 42, 44 and 46 bits. Read `PROTOCOL.md` first; it was frozen before any timing and
`sha256sum -c PROTOCOL.sha256` checks it.

| file | role |
|---|---|
| `PROTOCOL.md` | question, arms, workload, claim rule, predictions |
| `bench_glv_panel.c` | the timed program (`--fixture` builds public targets; the scalars never reach a timed run) |
| `make_panel.py` | builds the panels and manifests (seed 20261103) |
| `panel_<family>_<bits>.txt`, `manifest_<family>_<bits>.json` | frozen panels and Tier 1 manifests |
| `gh_manifest.py` | rewrites a frozen manifest for the GitHub runner (paths, pinned CPU, cgroup, identity) |
| `../../.github/workflows/glv-table-walltime-above40-tier1.yml` | builds the arms from pinned commits and runs `scripts/isolated_bench.py` |

This README was added after the freeze, in the commit that starts the workflow; it changes no frozen file.
Results follow in later commits (`REPORT.md`, `results.json`).

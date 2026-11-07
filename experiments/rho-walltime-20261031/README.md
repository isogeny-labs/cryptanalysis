# rho-walltime-20261031

Tier 1 wall time of #1327 (plain negation-map rho). Read `PROTOCOL.md` first; it was frozen before any
timing and `sha256sum -c PROTOCOL.sha256` checks it.

| file | role |
|---|---|
| `PROTOCOL.md` | question, arms, workload, claim rule, predictions |
| `bench_rho_panel.c` | the timed program (`--fixture` builds public targets; the scalars never reach a timed run) |
| `make_panel.py` | builds the panels and manifests (seed 20261101) |
| `panel_<bits>.txt`, `manifest_<bits>[_var].json` | frozen panels and Tier 1 manifests |
| `gh_manifest.py` | rewrites a frozen manifest for the GitHub runner (paths, pinned CPU, cgroup, identity) |
| `d32.patch` | the measurement arm `var`: #1327's head with the old DP spacing; not proposed |
| `../../.github/workflows/rho-walltime-tier1.yml` | builds the arms from pinned commits and runs `scripts/isolated_bench.py` |

This README was added after the freeze, in the commit that starts the workflow; it changes no frozen file.
Results follow in later commits (`REPORT.md`, `results.json`).

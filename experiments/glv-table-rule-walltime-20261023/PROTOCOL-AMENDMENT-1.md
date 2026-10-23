# Protocol amendment 1: Tier 1 host

**Committed before any Tier 1 timing.** It changes only the host. Everything
else in `PROTOCOL.md` stands: the panels, expected results, benchmark source,
measurement boundary, 15 alternating pairs per family, and the claim rule.

## Why

On 2026-10-23 at 21:07 UTC, the Runpod CPU pod rented under `PROTOCOL.md`
failed the Tier 1 preflight. That was pod `srwxamrnnf2mye`, flavor `cpu5c`:
4 vCPU of an AMD EPYC 4564P, Docker, kernel 6.8.0. It runs cgroup v1, so the
runner reported "declared cgroup is unavailable beneath cgroup v2" and the
missing `cpu.stat`/`memory.events`/`cpu.max`/`cpu.pressure` counters.
`isolated_bench.py run` rejected both manifests before any pair ran, so no
timing exists from that host.

The probe, rejection summaries and allocation receipt are kept in
`runpod-rejected-20261023/`. The pod was deleted after about one minute.

## New host

A GitHub-hosted `ubuntu-24.04` standard runner, started by
`.github/workflows/glv-table-rule-walltime-tier1.yml`. This is the repository's
existing Tier 1 path: the N83 E-1 receipts used it, with
`provider: github_actions`. The allocation receipt records the run ID,
attempt, runner image, observed CPU affinity and memory.

## Binaries

The runner rebuilds both binaries with `PROTOCOL.md`'s exact commands:

- **reference:** `cryptanalysis_static` at `7cb3dce`.
- **candidate:** `cryptanalysis_static` at `f630cc3`, which is `7cb3dce` plus
  #1065's `src/curve.c`.
- **both:** `cc -O3 -std=c11 -static` of `bench_glv_panel.c`, Release,
  `CA_NATIVE=OFF`, `CA_CUPQC=OFF`.

The workflow records their sha256 against the frozen hashes:

| arm | frozen binary sha256 |
|---|---|
| reference | `32630811…` |
| candidate | `43a89384…` |

If the runner's compiler produces different bytes, the run continues with the
runner's binaries, and the report says so. The frozen per-panel result hashes
(`1b2f4891…`, `13edb031…`) are checked by the runner on every pair either way.

`gh_manifest.py` rewrites the frozen manifests in the same way as
`pod_manifest.py`, but for GitHub Actions: paths, the pinned CPU (the lowest
CPU in the runner's affinity), the v2 cgroup, and the identity fields.

## Fix 1 (before any timing)

The workflow's first run (Actions run 40030129318) stopped in "Freeze runner
identity" with `KeyError: 'GLV_DIR'`. A variable written to `$GITHUB_ENV` only
exists from the next step on. That step now builds the receipt path from
`RUNNER_TEMP`. Nothing else changes, and no pair ran in the failed attempt.

## Fix 2 (before any timing)

Run 40036000239 built the reference library and then ran out of runner disk
while checking out the second full worktree (about 58,000 files). No pair ran.
The workflow now does three things differently:

- **Main checkout:** sparse, limited to `scripts/`, this experiment and `.github/`.
- **Pinned commits:** fetched blob-less at depth 1.
- **Arm worktrees:** each sparse-checks out only the directories CMake reads
  (`src`, `include`, `cmake`, `bindings`, `cuda`, `tools`, `tests`, `usecases`,
  `experiments/prime-j0-hot-orbit-table`, plus the root `CMakeLists.txt`).

The build commands and sources are unchanged.

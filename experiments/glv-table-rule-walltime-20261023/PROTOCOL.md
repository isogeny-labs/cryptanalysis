# Protocol: wall time of the GLV table rule c = 12 (Tier 1, Runpod CPU pod)

**Frozen before any timing on the pod.** This answers whether this PR's
operation-count gain (`experiments/glv-table-rule-confirm-20261022`:
geometric mean 0.957 for j = 1728 and 0.967 for j = 0, at 28–34 bits)
shows up in wall time. It follows AGENTS.md "CPU performance evidence tiers"
and `docs/ISOLATED_BENCHMARKS.md`, Tier 1.

## Workload

`make_panel.py` builds one frozen panel per family (`panel_j1728.txt`,
`panel_j0.txt`):

- **Curves:** 25 curves per size at r = 28, 30, 32 and 34 bits, sampled
  exactly as in the selection round.
- **Seed:** 20261024. It is fresh: no earlier run used it.
- **Targets:** 4 per curve, 400 per panel.

The panels hold only curves and public target points. The scalars stay out
of every file the binaries see. The expected result is the FNV-1a hash of the
true scalars in panel order, computed by `make_panel.py`:

| panel | expected result |
|---|---|
| j1728 | `1b2f48914f323ea1` |
| j0 | `13edb0311980828c` |

## Executable and timer

`bench_glv_panel.c` (reviewed source) is linked statically against each
library:

1. It sets up every group and target first. That part is outside the timer.
2. It then times, with `CLOCK_MONOTONIC` (`online_ms`) and process CPU time
   (`cpu_ms`), the sum of `ca_curve_solve` on each target plus a replay check
   (found · G == target).
3. It prints `verified=1` only if every replay matched, together with the
   operation total and the scalar hash (`result`).

The walk seed is 7 + target index.

| arm | library | binary sha256 |
|---|---|---|
| reference | `7cb3dce` unmodified, `cryptanalysis_static`, Release, `CA_NATIVE=OFF` (lib `82b52b08…`) | `32630811fe91ab72de1b352c90e28f721bfff462b8bb12c133eab3c0f4176afc` |
| candidate | `7cb3dce` + this PR's `src/curve.c` (lib `1d599388…`) | `43a8938471945ab61478b02e223ae668fe5e36700d6e6191782517901e15a98a` |

Both binaries come from the same compiler (gcc 13.3.0, Ubuntu 24.04) and the
same flags: `cc -O3 -std=c11 -static`.

## Host and gate

- **Host:** one Runpod CPU pod (compute-optimized flavor, `runpod/base`
  image), rented for this run and deleted afterwards. No SSH is used.
- **Boot:** `pod_boot.sh` accepts one payload whose sha256 is fixed in the
  pod's environment at creation. It writes the allocation receipt from the
  pod's own `RUNPOD_*` identity, with no API key.
- **Manifests:** `pod_manifest.py` rewrites only paths, the pinned CPU (the
  highest CPU the pod exposes), the cgroup and the instance identity in the
  frozen `manifest_<family>.json`.
- **Runner:** `scripts/isolated_bench.py run` (Tier 1) runs **15 alternating
  reference/candidate pairs** per family on that one pinned CPU.
- **Pair invalidation:** the runner's own gates invalidate any pair with a
  throttle, OOM, steal-time increment, major fault, failed verification,
  timeout, or changed input or source.

## Claim rule (the tier's own)

- **Report:** per family, the runner's median paired ratio (reference
  `online_ms` / candidate `online_ms`) with its deterministic 95% paired
  bootstrap interval.
- **Speedup:** a **Tier 1 speedup** is claimed only where the runner fills
  `paired_speedup`, which it does when the lower bound is above 1. Anything
  else is reported as measured, with no speedup claim.
- **Failed preflight:** if the pod fails the Tier 1 preflight, the run is
  kept and labelled exploratory. No tier is assigned.
- **The claim names:** the provider, the instance ID, the tier, the ratio, the
  interval and the observable limits.

## Also reported (not a claim)

- Each pair's operation totals, to check the panel reproduces the
  operation-count gain.
- `cpu_ms` alongside `online_ms`.
- An exploratory, untiered run of the same binaries and panels on the
  authoring VM: 4-vCPU KVM, cgroup v1, which fails the Tier 1 preflight.

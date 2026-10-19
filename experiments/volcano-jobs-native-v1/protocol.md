# `volcano --jobs`: independent native campaign protocol v1

**Status: frozen for review; no campaign timing has been collected.** This is
a new, independent comparison of the serial `ca volcano` CLI with the
`--jobs` implementation. It does not recover, reproduce, validate, or replace
the PR description's historical 0.205 s and 0.101 s observations. Those two
values remain an explicit, unresolved historical evidence gap in
[`volcano-jobs-historical-observation.md`](../../../docs/perf/volcano-jobs-historical-observation.md).

## Question and limits

Does running 36 seeded Pollard-rho solves through the candidate's native
`ca volcano --jobs 4` command reduce complete CLI wall time against the
serial baseline, while preserving the same KAT, 36 solve records, and exact
per-solve group-operation counts? This measures the CLI's job scheduling on
these two public workloads only. It makes no claim about the unknown curve or
command behind the historical PR timings, other curves, general rho
throughput, or cryptanalytic strength.

The primary workload has a new 33-bit prime-order subgroup and exactly 36
solves on four reserved CPUs, matching the historical summary's shape while
using independently fixed inputs. Its curve is supersingular (`j=0`, trace
zero), so the run is a CLI scheduling benchmark, not evidence about ordinary
volcano strata. The second workload exercises several measured arms and an
isomorphic control, also with 36 total solves. The PR's full CLI correctness
scope remains covered by its tests; this panel is specifically for the
parallel scheduling claim.

## Pinned code and builds

The baseline is the target branch tip `b3d9c4fdece5ff698581c478d646a50c61eef029`;
the candidate is the exact PR source commit
`d805fe6036bfefad6eabc74130df48366d4ae354`. The PR API returned base SHA
`2215b239685c0441eaad8a27c3f730d6a67f2d9f` at setup, an ancestor of the
target branch tip. The intervening commits changed research, Lean, and suite
files, not the native CLI, EC group, rho, or volcano sources. The campaign
uses the current fetched target branch tip as its baseline and records this
base-ref detail in [`build.json`](build.json).

Both sides use GCC 14.2.0, CMake 4.4.4, `Release`, `-O3 -DNDEBUG`, and
`CA_NATIVE=OFF`. The baseline and candidate binaries were built separately
with the same configure/build command and are pinned by SHA-256 in
`build.json`. The candidate binary's C sources match commit `d805fe6`; this
campaign wrapper and report do not change the candidate binary. The manifest
hashes both executables, the CMake caches, the relevant native sources, the
workloads, and all harness sources before and after the panel.

## Frozen public KAT workloads

`make_workloads.py` independently implements the checked-in deterministic
64-bit RNG and affine EC arithmetic used to derive each KAT. It emits
`workloads.json`, with fixed curve-order factorization, subgroup order,
generator, target, scalar, seed, and a SHA-derived workload ID. For the
primary curve, `n=4,418,424,173` is prime, `p=6n-1=26,510,545,037` is prime,
and `p=2 mod 3`; therefore `x -> x^3` permutes `F_p` and `y^2=x^3+1` has
exactly `p+1=6n` points. The small curve's point count is computed by the
Legendre-symbol sum in the generator and factored there.

| Workload ID | Curve and subgroup | Arms × trials | Total solves | Seed |
|---|---|---:|---:|---:|
| `6a74728c1fe0` | `y²=x³+1` over `p=26510545037`, `n=4418424173` (33 bits), cofactor 6, `ell=2` | 1 × 36 | 36 | 20261019 |
| `bfd2f4b95cf5` | `y²=x³+5x+17` over `p=1000033`, `#E=998368`, largest prime subgroup `n=4457`, cofactor 224, `ell=3` | 6 × 6 | 36 | 20261020 |

The known answers are fixed in `workloads.json`: scalar `3802224027` for the
33-bit case and `3928` for the six-arm case, together with their exact `P` and
`Q` coordinates. Every native run must return those values, report
`status=ok`, `wrong=0`, and provide 36 rows with the expected trial/arm
coverage and deterministic trial seeds. Base and candidate rows must have
the same SHA-256 of `(arm, vertex, level, trial, seed, ops)`; elapsed seconds
are deliberately excluded from that parity fingerprint.

## Paired command matrix and controls

`make_manifest.py` writes the host-specific frozen manifest. For each
workload, it creates three paired cases:

1. **A/A control:** baseline binary in both arms, with no `--jobs` option.
2. **Serial equivalence control:** baseline serial CLI versus candidate with
   `--jobs 1`.
3. **Parallel comparison:** baseline serial CLI versus candidate with
   `--jobs 4`.

The workload-specific solve arguments are fixed: primary uses
`--trials 36 --per-level 0 --controls 0`; multi-arm uses
`--trials 6 --per-level 2 --controls 1`. Every command also passes the
fixed `--p`, `--a`, `--b`, `--order`, `--ell`, `--seed`, `--threads 1`,
`--dp-bits 8`, and `--r 16` from the workload record. The wrapper adds
write-only temporary paths for the trials CSV and diagram JSON. It times the
native child process from immediately before `Popen` to process exit; parsing
and correctness checks are outside that timer.

There are 12 paired repetitions for every case, which exceeds the eight-pair
minimum. `scripts/isolated_bench.py` alternates the pair order by repetition:
`reference,candidate`, then `candidate,reference`, repeating ABAB for each
case (the first case's starting arm rotates by case index). Raw pair order is
retained in `pairs.jsonl`; no failed, noisy, or invalid pair may be silently
dropped. A speedup may be stated only if the paired 95% bootstrap interval
excludes 1 and the median log-ratio exceeds both the baseline A/A noise gate
(`2 × 1.4826 × median absolute log-ratio`) and `ln(1.02)`. Otherwise report
the measured ratio as inconclusive and make no speedup claim.

## Isolation gate and run procedure

No paid service or cloud allocation is part of this protocol. The only
qualified timing path is `tier0_host`, using a physical Linux host with the
repository's strict isolated-cgroup preflight. Reserve at least four complete
physical cores (including their SMT siblings) on one NUMA node; place the
single persistent benchmark service on housekeeping CPUs; pin benchmark
processes to all reserved CPUs through the new `execution_cpus` manifest
field; retain fixed-frequency, no-quota, IRQ, `nohz_full`, cgroup, CPU-steal,
interrupt, throttling, memory-failure, and context-switch checks. The existing
one-CPU manifest behavior remains the default for old studies. Four reserved
CPUs do not prove a fixed thread-to-core mapping; the claim is limited to the
audited exclusive CPU partition.

Before any timed command, the protocol, workloads, builds, wrapper, commands,
and harness will be committed and reported to the repository owner so the
shared workspace can receive a quiet window. Then, on the assigned host:

```sh
python3 experiments/volcano-jobs-native-v1/make_manifest.py \
  --cgroup /sys/fs/cgroup/benchmark-volcano-jobs \
  --cpus 4-7 --mem-nodes 0 \
  --output /workspace/volcano-jobs-native-v1/panel.json
python3 scripts/isolated_bench.py probe \
  /workspace/volcano-jobs-native-v1/panel.json
python3 scripts/isolated_bench.py --queue-root /workspace/isolated-bench \
  submit /workspace/volcano-jobs-native-v1/panel.json
```

The CPU IDs, NUMA node, and cgroup path above are examples; use only IDs
proved by that host's `probe-host` and strict preflight. If the preflight
rejects, no timed run starts and no lower tier is substituted. The current
managed executor's read-only probe reports a container, an active 4-CPU quota,
no isolated CPUs, no `nohz_full` CPUs, and no `numactl`, so it cannot run this
qualified protocol. No campaign timing has been taken here.

## Frozen outputs and reporting

The service output directory retains its exact manifest, preflight receipt,
host/build hashes, every stdout/stderr record, every raw trials CSV and
diagram input, `runs.jsonl`, `pairs.jsonl`, and service summary. Invalid and
failed rows stay in the record. A report and quantitative plot will be
generated only from those retained records, with a separate A/A noise panel
and per-workload paired ratio/95% interval. The standard volcano diagram is
rendered from the candidate's retained `volcano-diagram/v1` input; the report
labels the supersingular curve and the graph's scope. The campaign will also
add the report PDF and source graphs to `benchmarks/`, a dated row to
`benchmarks/README.md`, a separate CLI-panel entry to `docs/BENCHMARKS.md`,
and a non-weighted supplemental entry to `docs/perf/PERFORMANCE_INDEX.md`.
It will not change the library PI weights or the canonical index-calculus
volcano graphs: this CLI scheduling comparison changes no curve, isogeny,
ECDLP result, or library-kernel fingerprint. Those unchanged graph sets will
be audited explicitly in the result report.

# CPU baseline/A-A v6: fresh preparation and measurement design

Status: **design only; not a frozen protocol and not authorization to build or
measure**.  This document was written after
`../baseline-aa-v5-outcome.json` classified v5 as
`superseded_before_data/pre_data_infrastructure_loss`.  It creates no v6 run
root, imports no v5 artifact, and makes no timing claim.

The implementation MUST use a new namespace.  Nothing under
`baseline-aa-v5`, no v4/v5 binary, registry output, selection, tool directory,
runtime manifest, command plan, result row, or profiler output may be copied,
reconstructed, or accepted as v6 evidence.  The retained source identity and
scientific workload design below are study inputs, not v5 artifacts.

## 1. Outcome and scope

V6 asks one question only:

> Does one freshly sealed baseline executable pair produce an exact, fixed-N,
> byte-identical two-arm A/A null calibration over the complete frozen Rust/C
> panel at one and four threads without a false faster/slower verdict?

V6 does not authorize a candidate build, an optimization claim, or a
production speedup.  A candidate requires a later, prospectively frozen
A/B/A-prime protocol on a qualified placement.  V6 may establish that the
measurement machinery is exact and calibrated; its local wall clocks remain
nonqualified even when the campaign completes.

The replacement is deliberately split into two frozen records:

1. `cpu-baseline-aa-v6-preparation/v1` acquires and builds a completely new,
   content-addressed tool and benchmark bundle.  It forbids every benchmark
   `list`, `run`, correctness, timing, Callgrind, and perf invocation.
2. `experiment.protocol/v1`, protocol ID `cpu-baseline-aa-v6`, binds the
   published bundle byte-for-byte, the runner/analyzer byte-for-byte, and the
   complete command plan before the first registry or workload invocation.

An unresolved preparation value is a hard block, not a value the runner may
discover or choose.  A failed preparation is retained under its own root and
requires a new preparation version.  A failed or interrupted measurement
consumes its run ID and requires a new scientific protocol version; it is
never resumed or retried.

### Normative and literature basis

This design applies the repository's [experiment and CPU evidence
rules](../../../../AGENTS.md), the [tiered isolation
contract](../../../../docs/ISOLATED_BENCHMARKS.md), and the [performance-index
call boundary and statistics](../../../../docs/perf/PERFORMANCE_INDEX.md).
The cross-repository machine record is
`aburan28/crypto-autoresearcher@7e12aa99c3c652fc3918ed43c04617343345fb11:docs/experiment-protocol.md`
with its `experiment.protocol/v1` and `experiment.export/v1` schemas.

Hoefler and Belli, “Scientific Benchmarking of Parallel Computing Systems,”
SC15, [DOI 10.1145/2807591.2807644](https://doi.org/10.1145/2807591.2807644),
motivates fixed controls, full disclosure, paired samples, and reproducible
environments.  Mytkowicz et al., “Producing Wrong Data Without Doing Anything
Obviously Wrong!”, ASPLOS 2009,
[DOI 10.1145/1508244.1508275](https://doi.org/10.1145/1508244.1508275),
motivates closed environments, fresh processes, and byte-level build/layout
receipts.  Valgrind 3.28.0's “Setting Default Options” contract motivates
`--command-line-only=yes`; Linux `perf-config(1)` motivates
`PERF_CONFIG=/dev/null` plus the no-system/no-global guards.  These sources
justify the controls; none is performance evidence for v6.

## 2. Scientific constants that v6 preserves

### Source identity

The build input is exactly:

- commit `781722ef89e74b62079d2bc0cb82217061ac188c`;
- tree `99c6de3f3c617d1f16917bd81590279b167758da`;
- commit timestamp/SOURCE_DATE_EPOCH `1793565622`;
- Git archive SHA-256
  `a2031be1f2c1d3f00413b141757de370811c5c916321dcb72ad5513198bbbfb4`.

The fresh preparation independently recreates the archive from the public
commit and rejects any tree or archive mismatch.  It does not recover a lost
v4/v5 archive.  Git object mode and blob identity, not the active checkout's
materialized mode, bind source files.  These key source hashes are additional
full-call guards:

| file | SHA-256 |
| --- | --- |
| `suite/examples/perfbench/harness.rs` | `0a47e712de15a1e0376ab431c447a9c145753444983c7639e8801ce26ae5692e` |
| `suite/examples/perfbench/main.rs` | `27b3240afce35b6032874b7b793fea7b9f4cb7c56957494bd145d6f5567d2429` |
| `tools/ca_perfbench.c` | `90becdfad3f93e812b6ad465668d4f03c942b5237c19d4e2a5497eed06891edc` |
| `scripts/perf/perfindex.py` | `28084cd77fe28d3b031f4dc1474241ee051b2072c7b62dc7a17e0049c3e3674f` |
| `docs/perf/weights.json` | `5d1ffd7585b6bf145817402f45fe122b97468ba64a2e50ea939ae469945b9ca4` |
| `suite/Cargo.toml` | `79215eaaee65fc415a83ca20006ddf541a3a76dd2bdc84f774b2f749a1080cf1` |
| `suite/Cargo.lock` | `cffcbfacc10d859ca8269e8e5b7142f0eea39f178766b90f185f0ec314db6115` |
| `CMakeLists.txt` | `9e880cfcee47d18c26f793f4b4a15a1737b6f55b2250016b4e1c264e50f51fca` |

The complete `suite/examples/perfbench` Git tree is
`c4e6ca726a7d5fe5662e965021e1f6b50093e254`.

### Frozen cells

Every cell is included; there is no registry-driven selection.

Rust, in this declared order (10):

1. `gf2_la/rref_random_4940x8357`
2. `gf2_la/rref_macaulay_k5m3d5`
3. `gf2_la/echelon_macaulay_k5m3d5`
4. `bool_gb/matrix_f5_deg4_m2_n23`
5. `bool_gb/solve_matrixf5_m2_n17`
6. `field_ec/f2m_mul_sqr_m131_64k`
7. `field_ec/f2m_mul_sqr_m163_64k`
8. `field_ec/f2m_mul_sqr_m233_64k`
9. `field_ec/f2m_inv_m163_2k`
10. `field_ec/binary_scalar_mul_sect163k1_x8`

C, in this declared order (34):

1. `field_ec/c_mont_mul_x8`
2. `field_ec/c_zp_op_chain`
3. `field_ec/c_powmod`
4. `field_ec/c_mont_pow`
5. `field_ec/c_invmod`
6. `field_ec/c_sqrtmod`
7. `field_ec/c_is_prime`
8. `field_ec/c_factorize`
9. `field_ec/c_ec_add_chain`
10. `field_ec/c_ec_batch_add`
11. `field_ec/c_ec_scalar_mul`
12. `field_ec/c_ec_count_points`
13. `dlp/c_rho_ec36`
14. `dlp/c_rho_ec44`
15. `dlp/c_rho_ec44_mt`
16. `dlp/c_rho_zp40`
17. `dlp/c_kangaroo_ec56_w34`
18. `dlp/c_kangaroo_zp61_w36`
19. `dlp/c_bsgs_ec32`
20. `dlp/c_bsgs_zp36`
21. `dlp/c_grumpy_ec32`
22. `dlp/c_pohlig_ec48s`
23. `dlp/c_pohlig_zp61s`
24. `dlp/c_precomp_build_ec32`
25. `dlp/c_precomp_online_ec32`
26. `dlp/c_glv_rho_j0_32`
27. `dlp/c_gpu_rho_emulate_ec32`
28. `dlp/c_cheon56`
29. `relation/c_ic_precompute_zp44`
30. `relation/c_ic_precompute_zp52`
31. `relation/c_ic_randexp_zp36`
32. `relation/c_ic_log_zp44`
33. `relation/c_linsolve_sparse`
34. `relation/c_dense_solve`

The live registries are invoked only after the data protocol is frozen.  Rust
`list` may contain other source-defined Quick kernels, but IDs must be unique
and its exact-ID projection must contain all and only the ten frozen rows,
each with the frozen Quick tier, area, and description.  Unselected Rust rows
never enter the plan.  C `list --full` must return exactly the 34 frozen rows,
with unique IDs and frozen areas/descriptions.  Missing, duplicate, or
additional selected IDs terminate v6 with zero wall or profiler calls.  A
live registry contradiction is invalid provenance, not an excuse to alter the
list.

### Full-call and correctness gates

Only the complete timed `Workload::run` boundary in the Rust harness and the
complete `k->run` boundary in the C harness are wall observations.  Setup,
input restoration, build time, phase time, profiler time, and report time are
never substitutes.  Callgrind client requests must enclose that same complete
run boundary.

Every successful invocation must satisfy all of the following before its
clock is interpreted:

- exit status zero, no timeout, exactly one JSON object, and exact requested
  ID;
- nonempty fingerprint and the same fingerprint across both labels, all six
  rounds, both thread panels, and every successful diagnostic for that ID;
- three through five positive `samples_ns` values, with `median_ns` exactly
  the harness's integer median and `min_ns` exactly their minimum;
- the source, binary, registry row, thread count, affinity, seed, budgets, and
  exact-selector values hash to the frozen work-contract preimage;
- no sample is accepted from setup, warmup, a partial stage, emulation that is
  presented as hardware, or a resumed process.

The explicit harness arguments are `--samples 5 --min-samples 3
--max-seconds 2.0 --warmup-seconds 0.2`.  Warmup performs at least one full
call and continues until 0.2 seconds, but is discarded and creates no export
row.  Each fresh benchmark process emits one row.

## 3. Fresh, reproducible preparation

### Source lock and known tool pins

Preparation starts in an empty, versioned root such as
`/workspace/.benchmarks/performance-saturation/cpu/baseline-aa-v6-prep-<PREP_SHA12>`.
It never reads a v4/v5 build or `/workspace/.tools`.

The preparation source lock must contain URL, version/tag/commit, byte size,
SHA-256, signature URL/hash, and verified signer fingerprint when the
upstream signs releases.  The following values are already fixed:

| component | exact input |
| --- | --- |
| Rust | `rust-1.99.1-x86_64-unknown-linux-gnu.tar.xz`, `https://static.rust-lang.org/dist/2026-10-15/rust-1.99.1-x86_64-unknown-linux-gnu.tar.xz`, SHA-256 `231fcae47ee950621374725b5fc3b5441d2fbda2955ac45dd7dc816d8876cfe7` |
| Rust channel manifest | `https://static.rust-lang.org/dist/channel-rust-1.99.1.toml`, SHA-256 `fb152be80975c194aa5fc684b2aec3a6e14e2b855efe2faa4e5f8ae6e590f463` |
| CMake | PyPI wheel `https://files.pythonhosted.org/packages/0b/d0/18fe62f0bddc8b9bb71ba55762ee48a224f8344101c34350d969f6e0d327/cmake-4.4.3-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl`, size 30,231,983, SHA-256 `bae3c4954623ec4d62e62c70443f0da7988b733111c2871fcc6a31ead5137e20` |
| Valgrind | version 3.28.0, `https://sourceware.org/pub/valgrind/valgrind-3.28.0.tar.bz2`, plus its detached signature |
| Linux perf source | signed tag `v6.12.113`, tag object `0f6a69bb2f85d6da4dc81c32685143ee6c255348`, peeled commit `7fdb7c1824a1f9979d648d7ae28ac446bcee9c6e` |
| canonical protocol tool | `crypto-autoresearcher` commit `7e12aa99c3c652fc3918ed43c04617343345fb11`; tool SHA-256 `0f46a2b856bb1df2d155c4a676b46c6118d82c45cf8e5cc0492315aeb45c84e4`; protocol schema `a9b948f2be323f862b98301eb7a5aa147ecc29db35041737f0aa3dfd03ad2443`; export schema `108f0ae9c1be3ed141bca3c22216eba049f2c76677f11013109a4740f19bd757` |

Before the preparation record can freeze, it MUST additionally resolve and
bind:

- the actual Valgrind archive size/SHA-256, signature SHA-256, and trusted
  signer fingerprint;
- a Linux source archive produced from the signed perf tag and its SHA-256;
- one build OCI manifest digest (never a mutable tag), its architecture, and
  a complete package/version manifest for GCC, binutils, make, libc headers,
  libelf/libdw/libunwind/zstd and other perf/Valgrind build dependencies;
- a relocatable CPython distribution URL/version/size/SHA-256, or an
  equivalently complete freshly built Python runtime, for stdlib-only
  controller and analyzer execution;
- every Cargo archive named by the frozen `suite/Cargo.lock`, with checksum
  equality to the lockfile, and a canonical manifest digest of the vendored
  tree;
- exact Valgrind and perf configure/build/install argv, their dependency
  closure, and the hash of every executable/DSO shipped in the runtime
  bundle;
- the immutable public artifact transport and read-back command used to
  publish the completed bundle.

Those are declared resolution gates, not TODOs the data runner may fill.  No
preparation freeze and therefore no build is permitted while any is null.

### Build isolation and commands

All preparation work that can consume CPU holds
`/workspace/.benchmarks/performance-saturation/local/global-cpu.lock` with an
exclusive `fcntl.flock` for its entire process lifetime.  Network resolution
and downloads finish before compilation.  Compilers run only inside the
frozen OCI image, with the source mounted at `/work/src`, vendor input at
`/work/vendor`, and output at `/work/out`.  The exact inherited-nothing base
environment is:

```text
env -i HOME=/nonexistent LANG=C LC_ALL=C TZ=UTC PATH=<FROZEN_TOOL_PATH>
SOURCE_DATE_EPOCH=1793565622 CARGO_NET_OFFLINE=true CARGO_INCREMENTAL=0
CARGO_BUILD_JOBS=1
```

The Cargo configuration replaces crates.io with `/work/vendor` and sets
offline mode.  The Rust build command is prospectively fixed as:

```text
cargo build --manifest-path /work/src/suite/Cargo.toml \
  --release --locked --offline --example perfbench
```

`RUSTFLAGS` contains only the exact preparation-frozen path remap
`--remap-path-prefix=/work/src=/usr/src/cryptanalysis` and
`-C debuginfo=0`; it must not contain `target-cpu=native`, unregistered target
features, PGO, or ambient flags.

The C build uses a one-job Unix Makefiles generator and exact paths to the
frozen compiler and make:

```text
cmake -S /work/src -B /work/out/c-target -G 'Unix Makefiles' \
  -DCMAKE_BUILD_TYPE=Release -DCA_BUILD_SHARED=OFF \
  -DCA_BUILD_STATIC=ON -DCA_BUILD_TOOLS=ON -DCA_BUILD_TESTS=OFF \
  -DCA_NATIVE=OFF -DCA_CUDA=OFF -DCA_CUPQC=OFF -DCA_FUZZ=OFF \
  -DCMAKE_C_COMPILER=<FROZEN_GCC> -DCMAKE_MAKE_PROGRAM=<FROZEN_MAKE> \
  -DCMAKE_C_FLAGS_RELEASE='<FROZEN_O3_NDEBUG_AND_PATH_REMAP_FLAGS>'
cmake --build /work/out/c-target --target ca_perfbench --parallel 1
```

The preparation record replaces every angle-bracket token above with one
absolute in-image path/string and binds the canonical argv-array SHA-256.
The baseline source's own harness is used directly; no current-tree overlay
or appended CMake stanza is allowed.

Rust and C are each built twice in two new containers with the same mounted
paths and empty output trees.  The two `perfbench` hashes must match and the
two `ca_perfbench` hashes must match.  A mismatch blocks preparation; neither
copy may be selected after inspection.  The first copy is retained only when
both pairs match.  Valgrind and perf are likewise built from their locked
sources with their frozen commands, and their installed manifests are
compared across two clean builds.  Build failures, logs, exit status, image
digest, `/proc/self/status`, and output inventory are retained once.  A
recipe change is a new preparation version, not a retry under the old one.

Build staging may run compiler/version checks and hash/read-only ELF
inspection.  It MUST NOT invoke either benchmark binary with `list`, `run`,
`--instr`, or any other workload path, and MUST NOT invoke Callgrind or perf
on a benchmark.

### Bundle and runtime closure

The published bundle contains, at minimum:

- the source archive, source-lock, Cargo archives/vendor tree, exact build
  recipe, OCI digest/package manifest, and all raw build logs/receipts;
- the fresh Rust and C benchmark binaries and their build manifests;
- the relocatable stdlib-only Python runtime;
- the fresh Valgrind/Callgrind and perf executables, their private libraries,
  ELF interpreters/DSOs needed at run time, licenses, and build manifests;
- the new single-file v6 runner, analyzer, snapshotter, and their synthetic
  crash/command-plan tests;
- the pinned canonical protocol tool and schemas.

Its manifest addresses relative paths only and records type, byte count,
normalized mode, and SHA-256.  Directories are `0755`, executable files
`0755`, and nonexecutables `0644`; symlinks, device files, absolute paths,
and hard links are rejected.  This avoids treating a checkout's incidental
`0600`/`0644` materialization as source identity.

The archive algorithm is frozen in the preparation record: sorted relative
paths, ustar/PAX choice fixed, uid/gid zero, empty owner/group names, mtime
zero, no atime/ctime extensions, and deterministic compression with timestamp
and original filename disabled.  The archive SHA-256, byte size, manifest
canonical SHA-256, public immutable URI/ref, and a successful downloaded
read-back hash are committed before the data protocol is drafted.  The run
extracts it to
`/workspace/.benchmarks/performance-saturation/cpu/baseline-aa-v6-tools-<BUNDLE_SHA12>`
and verifies every entry before use.  No build fallback exists.

## 4. Canonical protocol mapping

The eventual `experiment.protocol/v1` has four arms:
`base-1t`, `base-aa-1t`, `base-4t`, and `base-aa-4t`.  The paired arms at each
thread count bind the same absolute executable and SHA-256.  It declares 44
instances, six replicates, four arms scoped by language/thread applicability,
zero exported warmups, and exactly 1,056 measured execution cells.  Seed
derivation is the frozen harness rule starting at 20260926.

Primary metrics are exact fingerprint equality, work-contract equality,
complete-invocation count, complete-pair count, and false-direction count.
Full-call wall nanoseconds and paired ratios are secondary, explicitly
nonqualified metrics.  Callgrind/perf metrics are diagnostic.  The decision is
fixed-N; there is no optional stopping, rank-test p-value, candidate effect, or
power claim.  The power field therefore records a non-inferential calibration
rationale rather than pretending 88 cells are a sampled population.

The byte-identical A/A panel is the negative/null control.  No positive
control is introduced because v6 makes no sensitivity or candidate-speedup
claim, and adding a synthetic delay would change the registered workload; the
canonical control field gives that reason.  Label masking cannot hide two
byte-identical arms and is not claimed as analyst independence.  Bias control
comes from a frozen analyzer, mirrored order, fixed N, exact gates, and an
independent raw-row replay.

The execution backend is local, no checkpoint, no restore, and no
infrastructure retry after root creation.  Failures are export rows.  Before
freeze, `sample_size.preflight_runtime` receives a conservative planning
estimate derived from the frozen 0.2/2.0-second harness budgets, process and
30-second barrier counts, 1,800/86,400-second timeout ceilings, and separately
identified profiler allowances.  It is not obtained by an unregistered
benchmark probe and is not evidence.  The analysis path and SHA-256, all
stopping/decision rules, and every inadmissible move are non-null before the
canonical tool freezes the protocol.

## 5. Measurement qualification

The local v6 protocol is permanently `nonqualified` because it has no
provider allocation receipt or proof of exclusive physical-host CPUs, fixed
frequency, NUMA/memory policy, IRQ routing, SMT placement, or host-wide
absence of competing work.  Container affinity and the global lock do not
upgrade it.  Every exported wall row therefore has `wall_valid: false` and
`tier: nonqualified`, even if all internal noise checks are quiet.

Evidence is classified as follows:

| evidence | admissible use in local v6 |
| --- | --- |
| source/binary/tool hashes, exact registries, fingerprints, work-contract and row counts | admissible exact/count evidence for protocol adherence, not a timing tier or speedup |
| complete-call wall medians, ratios and bootstrap intervals | descriptive nonqualified A/A calibration only |
| Callgrind `Ir` inside the complete marked region | deterministic mechanistic diagnostic when its tool/command/fingerprint gates pass; never wall time |
| perf software events (`task-clock`, `cpu-clock`, context switches, page faults) | nonqualified diagnostic only |
| `perf record` `cpu-clock` samples/callchains | nonqualified explanatory diagnostic only |
| setup/build/stage/profile duration | operational metadata only |

A later Tier 0 run needs an auditable physical-host receipt covering CPU/SMT
topology, NUMA, exclusive partition, affinity, memory policy, fixed frequency,
IRQ routing, quota, hashes, order, failures, throttling, steal, interrupts,
and correctness.  A later Tier 1 run needs a provider/instance allocation
receipt, same-instance paired arms, affinity, process CPU/memory, cgroup
throttling/OOM, steal and scheduling counters, repeated alternating pairs,
and a 95% paired interval whose lower bound exceeds one.  Either is a new
protocol; v6 evidence cannot be promoted after collection.

## 6. Fixed command plan

### Placement, lock, and environment

The controller acquires the global lock before creating the run root and
holds the same file descriptor until the campaign terminates.  It pins itself
and all snapshot/upload work to CPU 4.  It reserves CPUs 0-3 for the complete
campaign; one-thread children run on CPU 0 and four-thread children on CPUs
0-3.  Preflight requires CPUs 0-4 in the effective cpuset.  Any other topology
is a zero-data operational block and cannot trigger a different placement.

The controller is a stdlib-only, single-file program launched by the bundled
Python as `-I -S -B -P` from `env -i`.  Benchmark environments contain only
the frozen loader/library path plus:

```text
LANG=C LC_ALL=C TZ=UTC PYTHONHASHSEED=0 PYTHONCOERCECLOCALE=0 PYTHONUTF8=1
RAYON_NUM_THREADS=<1-or-4> OMP_NUM_THREADS=<1-or-4>
OPENBLAS_NUM_THREADS=1
```

No `HOME`, `RUSTFLAGS`, `VALGRIND_OPTS`, ambient `PERF_CONFIG`, preload, or
user configuration is inherited.  Every executable path is absolute inside
the verified bundle.  Children start in a new process group.  The controller
sets affinity before `execve`, never after the workload can begin.

The isolation receipt samples every five seconds and retains the raw inputs
used to compute each result.  It records all PIDs whose affinity intersects
0-3, campaign ancestry, `/proc/<pid>/stat` CPU deltas, per-CPU `/proc/stat`,
interrupts/softirqs, pressure files, load, cgroup `cpu.max/cpu.stat`, cpuset,
memory events/limits, pids, governors/frequencies, topology, steal, migrations,
and throttling.  The primary other-work counter is robust to short-lived
processes: from the aggregate non-idle jiffies on CPUs 0-3, subtract cumulative
campaign user/system CPU (live descendant stats plus controller-retained
`wait4` usage for exited descendants).  Divide the remainder by elapsed
monotonic seconds; any five-second interval above `0.10` core-equivalents is
contention.  PID enumeration is a corroborating inventory, not the only
accounting source.  An aggregate/campaign accounting gap, PID-reuse ambiguity
inside campaign ancestry, wrong affinity, nonzero cgroup throttled-time delta,
OOM event, nonzero steal delta on reserved CPUs, or a campaign descendant left
alive is also operationally incomplete.  Missing frequency, IRQ, PSI, or
physical-host observables is retained as a qualification limitation; it can
never turn local clocks valid.

Before each wall session the fixed barrier is 30 quiet seconds.  There is no
adaptive extension: a failed quiet barrier consumes the run as operationally
incomplete.  Each child has a 1,800-second timeout.  An outer wall session or
diagnostic attempt has an 86,400-second timeout.  Timeout handling sends
SIGTERM to the process group, waits exactly ten seconds, sends SIGKILL, waits,
and records both actions.

### Wall schedule

Session order is exactly:

1. Rust, one thread, CPU 0;
2. C, one thread, CPU 0;
3. Rust, four threads, CPUs 0-3;
4. C, four threads, CPUs 0-3.

Each session constructs a fresh CPython `random.Random(20260926)`.  It sorts
that language's IDs by Unicode code point, and for rounds 0 through 5 copies
and shuffles the sorted list once.  Every cell then runs A/B in rounds 0, 2,
and 4 and B/A in rounds 1, 3, and 5.  A and B resolve to the same absolute
binary and the same SHA-256.  The complete generated array and canonical JSON
SHA-256 are persisted in the protocol before data; generation at run time must
equal it exactly.

There are exactly:

- `10 * 2 * 6 * 2 = 240` Rust measured invocations;
- `34 * 2 * 6 * 2 = 816` C measured invocations;
- 1,056 total measured invocations, 88 thread/cell analyses, and six mirrored
  pairs per analysis.

The first failed, timed-out, contended, malformed, or in-flight wall attempt
stops the remaining wall and every profiler phase.  It is retained once; no
replacement, resume, or infrastructure retry is allowed.  Fixed-N means no
early success stop and no result-dependent extension.

### Callgrind diagnostics

Only after all 1,056 wall invocations and all wall isolation gates complete,
attempt 88 one-thread Callgrind children: the ten Rust IDs lexicographically,
then the 34 C IDs lexicographically, and A then B for each.  Each command is:

```text
<valgrind> --command-line-only=yes --tool=callgrind \
  --callgrind-out-file=<EXCLUSIVE-TEMP-RAW-FILE> --instr-atstart=no \
  <same-binary> run --filter <EXACT_ID> --exact --instr
```

It is pinned to CPU 0.  On a terminal child, the exclusive temporary raw file
is flushed, fsynced, and renamed to its prospectively bound final path; an
interruption retains the temporary file and may not reuse it.  The raw
Callgrind file, stderr `Collected` count, one benchmark JSON row, fingerprint,
command, environment, and tool/DSO hashes are retained.  `Ir` must be a
positive integer and A/B fingerprints must equal the wall fingerprint.  An
ordinary diagnostic failure is retained and later Callgrind/perf-stat attempts
continue; an operator/controller interruption stops the exact remaining
diagnostic suffix.

### perf diagnostics

After all 88 Callgrind attempts have terminal receipts, attempt 88 CPU-0
`perf stat` children in globally lexicographic cell order, A then B.  The only
events are:

```text
task-clock,cpu-clock,context-switches,page-faults
```

The command uses `-x, --no-big-num`, a prospectively bound output path, and
the benchmark arguments `--samples 5 --min-samples 5 --max-seconds 2.0
--warmup-seconds 0.2`.  Every perf acquisition and offline parser receives
`PERF_CONFIG=/dev/null`, `PERF_CONFIG_NOSYSTEM=1`, and
`PERF_CONFIG_NOGLOBAL=1`; no hardware PMU event is requested or imputed.

After all perf-stat terminals, derive the eight perf-record commands.  Slots
1-3 are fixed in this order:

1. `gf2_la/rref_random_4940x8357`
2. `bool_gb/matrix_f5_deg4_m2_n23`
3. `field_ec/f2m_mul_sqr_m163_64k`

Slots 4-8 are the five C IDs with largest strictly positive baseline-A
Callgrind `Ir`, sorted by descending `Ir` and then ascending complete ID.  All
34 valid baseline-A C counts are required.  The selected IDs, full argv array,
and its canonical digest are durably written before slot 1.  If any selection
input is missing/invalid, the entire perf-record phase is `not_attempted`; no
fixed slot or substitute is run.

Each selected baseline-A command is pinned to CPU 0 and uses:

```text
perf record -e cpu-clock -F 99 -g --call-graph dwarf \
  -o <EXCLUSIVE-TEMP-DATA-FILE> -- <same-binary> run --filter <EXACT_ID> \
  --exact --samples 5 --min-samples 5 --max-seconds 2.0 \
  --warmup-seconds 0.2
```

On a terminal child, the temporary perf output is flushed, fsynced, and
renamed to the frozen final name; an interrupted temporary is retained and is
not a successful profile.  The frozen perf must parse every successful final
file with `perf evlist` and `perf script` under the same closed configuration.
A successful profile has the `cpu-clock` event, at least one sample, and at
least one callchain frame.  Profiler output never changes a wall verdict.

The diagnostic schedule is one exact prefix: 88 Callgrind terminals, 88
perf-stat terminals, then zero or eight perf-record terminals.  Non-prefix,
reordered, duplicate, or later evidence after an interruption is invalid
provenance.

## 7. Crash-atomic result and remote evidence model

The run root is
`/workspace/.benchmarks/performance-saturation/cpu/baseline-aa-v6/<RUN_ID>`.
It is created once with exclusive directory creation only after the global
lock is held.  A pre-existing path refuses execution.  `plan` is pure: it
executes no child and writes nothing.

All JSON is UTF-8 canonicalized with sorted keys, comma/colon separators,
finite numbers only, and a trailing newline.  A durable write-once object is
created as a same-directory exclusive temporary file, flushed and `fsync`ed,
atomically renamed to its final name, then followed by directory `fsync`.
Existing final or temporary names are fatal.  Consolidated journals and
summaries are derivatives; per-attempt objects are authoritative.

For every child the controller, in order:

1. durably writes `started.json` with sequence, phase, command, exact
   environment, hashes, affinity, work-contract, and monotonic/wall start;
2. opens exclusive `stdout.partial`/`stderr.partial` and profiler-temporary
   paths and spawns a new process group;
3. durably writes `launched.json` with PID and PGID;
4. waits or performs the frozen timeout kill sequence;
5. flushes/fsyncs raw streams, renames completed streams/profiler output to
   their final names, fsyncs the directory, hashes them, and verifies no
   descendant remains (a controller crash leaves immutable `.partial` files);
6. durably writes exactly one `terminal.json` with exit/timeout/parse status,
   hashes, row or failure, isolation slice, and finish times.

An absent terminal after a start is `interrupted`, not an invitation to rerun.
No acquisition command has a resume mode.  `finalize` is analysis-only,
requires an explicit proof that no campaign process is live, and may create a
new numbered analysis attempt without changing raw evidence.  The first valid
frozen-analyzer export is write-once.  A later analyzer correction is a new
versioned record naming the old output.

Because v5 was lost before durable publication, v6 adds fixed evidence
barriers.  After preflight and after each of the four wall sessions, the
controller creates a deterministic snapshot of the authoritative prefix on
CPU 4, uploads it to the preregistered immutable remote location, downloads
it, verifies SHA-256, and durably records the receipt.  It does the same after
Callgrind, perf-stat, perf-record/not-attempted, and finalization.  Snapshot
failure stops the campaign; it never authorizes resume.  The next wall quiet
barrier occurs after snapshot/upload and therefore prevents upload activity
from overlapping a measured child.  A lost local root can be audited from its
last snapshot but remains incomplete and may not be continued.

## 8. Frozen analysis and terminal decisions

The new analyzer reads raw per-attempt objects; it does not trust a runner
summary.  A second implementation reconstructs the schedule, sample medians,
fingerprint sets, exact row count, isolation gates, and every statistic.

For cell `k`, thread panel `p`, and round `r`, define
`d[k,p,r] = ln(median_A / median_B)`.  The cell speedup is
`exp(median(d))`.  The percentile interval uses exactly 2,000 bootstrap
resamples of the six paired rounds.  Analysis RNG is separate from scheduling:
its integer seed is the big-endian SHA-256 value of
`b"cpu-baseline-aa-v6-analysis\0" + session_id.encode("ascii")`.  The lower
index is `int(0.025*2000)` and the upper index is
`int(0.975*2000)-1` in the sorted bootstrap values.  A cell is `faster` only
if the log interval is wholly above zero and its median exceeds `ln(1.02)`;
it is `slower` symmetrically; otherwise it is `neutral`.  Area/index values
use the frozen `weights.json` and are descriptive only.  No p-value or clock
can override an exactness failure.

Terminal precedence is exact:

1. any candidate build, arm, output, or comparison:
   `not_authorized_candidate_comparison`;
2. contradictory source/bundle/tool/command/schedule/registry/fingerprint or
   non-prefix evidence: `invalid_exactness_or_provenance`;
3. a clean static preflight block with zero registry/wall/profile calls:
   `blocked_artifact_or_placement`;
4. any missing/in-flight/failed/contended wall attempt, fewer than 1,056
   complete invocations, fewer than six pairs in any of 88 analyses, failed
   evidence barrier, or adverse isolation receipt:
   `inconclusive_contention_or_incomplete`;
5. a complete exact wall panel with any independently replayed directional
   cell: `baseline_aa_false_direction_nonqualified`;
6. a complete exact wall panel with all 88 cells neutral:
   `baseline_aa_complete_nonqualified`.

Profiler failures are separately reported and cannot demote or promote an
otherwise complete wall outcome.  Profile schedule completeness requires all
planned terminal receipts (or the one preregistered whole-phase
`not_attempted` perf-record receipt), but it is not a speedup gate.

The canonical `experiment.export/v1` has 1,056 measured wall rows and zero
warmup rows.  Failures/cancellations fill the remaining planned execution
cells with their actual status; they never masquerade as completed calls.
Every row binds protocol hash, bundle hash, source/binary hash, work-contract,
run ID, arm, instance, replicate 1-6, seed 20260926, host receipt, and raw file
hash.  `check-export --verify-files` must pass before publication.

## 9. Exact preregistration and execution sequence

No step may be reordered:

1. Commit and publish the v5 outcome record; verify the v5 result root remains
   absent and its acquisition counts are zero.
2. Resolve every preparation source-lock field listed in section 3 without
   building or invoking a benchmark.  Write the preparation controller and
   synthetic tests.
3. Write `preparation-v6.json` as draft.  Its forbidden-command list includes
   both benchmark paths and `list`, `run`, `--instr`, Callgrind, and perf.
   Canonicalize the source lock, build argv arrays, environment, expected
   outputs, failure policy, and new preparation root.
4. Run only preparation schema/unit/synthetic checks.  Commit the draft and
   tooling as registration commit `P0`; push it and verify it from the remote.
5. Freeze preparation against `P0`, commit the frozen record as `P1`, push,
   and verify both commits remotely.  Only then acquire/build under the global
   lock.
6. Execute preparation once.  On success, seal and publish the deterministic
   bundle, download it to an empty directory, verify every manifest entry and
   the whole archive, and commit a write-once preparation outcome.  On any
   failure stop; do not proceed with a partial bundle.
7. From the verified bundle identities, write new v6 runner, analyzer,
   snapshotter, command-plan generator, and tests.  Generate the entire wall
   and diagnostic plan twice in clean processes and require byte equality.
   Fill every binary/tool/runtime/plan/schedule/output identity in the
   canonical `experiment.protocol/v1`; no null artifact field remains.
8. Run only unit, synthetic crash-atomic, hostile-environment, parser, and
   pure-plan tests.  These tests use fake children and fixtures, never a
   benchmark binary.  Validate the draft with the sealed canonical tool.
9. Commit the draft protocol plus exact runner/analyzer/tests as registration
   commit `D0`; push and remote-verify it.  Invoke the sealed canonical tool:

   ```text
   <SEALED_PYTHON> -I -S -B -P <SEALED_EXPERIMENT_PROTOCOL> \
     freeze protocol-baseline-aa-v6.json --commit <D0> \
     --filed-before-affected-data
   <SEALED_PYTHON> -I -S -B -P <SEALED_EXPERIMENT_PROTOCOL> \
     validate protocol-baseline-aa-v6.json
   ```

10. Commit the frozen protocol as `D1`, push, and remote-verify `D0`, `D1`,
    the protocol hash, analysis hash, and bundle URI/hash.
11. Generate one 128-bit run nonce before acquisition and write
    `run-intent.json` containing the nonce hash, run ID, protocol hash, bundle
    hash/URI, complete plan digest, fixed root, local-nonqualified class,
    placement, and exact launch argv.  Commit/push/read-back this intent as
    `D2`.  The nonce affects only run identity, never schedule or analysis.
12. Invoke pure `plan` and require exact equality with the protocol.  Acquire
    the global lock.  Once the create-once root and durable `started.json`
    exist, v6 is consumed.
13. Verify every bundle entry and host/placement invariant; capture the initial
    system receipt; invoke the two registries; persist and remotely snapshot
    preflight.  A mismatch terminates before wall data.
14. Execute the four wall sessions, each followed by its mandatory remote
    snapshot; then the Callgrind, perf-stat, selection/perf-record, and final
    snapshot phases in the fixed order.
15. Prove no campaign process is live.  Run the frozen analyzer, build and
    validate the export with file verification, seal the final deterministic
    evidence archive, upload/read-back verify it, and commit/push a small
    outcome record containing verdict, counts, archive URI/size/SHA-256,
    protocol/bundle hashes, and all qualification limits.
16. Obtain an independent `experiment.review/v1` adherence/recompute/scope
    review.  The review may replay analysis from raw rows but may not rerun a
    workload under v6.

At steps 5, 10, 11, and 15, failure to publish/read back is a stop.  Local-only
registration or evidence is insufficient after the v5 infrastructure loss.

## 10. Required implementation files and acceptance gates

All implementation files live under a new
`experiments/performance-saturation-20261101/cpu/baseline-aa-v6/` directory;
none replace this design or a v5 file.  Required files are:

- `preparation-v6.json` and a preparation runner with custom schema/tests;
- `source-lock-v6.json`, `build-recipe-v6.json`, and bundle manifest/schema;
- `protocol-baseline-aa-v6.json` (`experiment.protocol/v1`);
- `run_cpu_baseline_aa_v6.py`, `analyze_cpu_baseline_aa_v6.py`, and
  `snapshot_cpu_baseline_aa_v6.py`, each stdlib-only and separately hashed;
- command-plan, receipt, work-contract, preparation, and outcome JSON schemas;
- synthetic fake-child fixtures and tests for pure plan behavior, hostile
  environment closure, O_EXCL/create-once semantics, fsync/rename ordering,
  interruption at every write boundary, PID/PGID kill handling, schedule
  reconstruction, profiler prefix rules, selection, and independent analysis;
- a short report template that separates exact/count evidence, nonqualified
  clocks, diagnostics, failures, and qualification limits.

Implementation is ready to register only when all of these gates pass:

- no v4/v5 runtime path appears anywhere in the v6 source lock, bundle,
  protocol, plan, or result-root string;
- every source/tool/build/runtime identity is non-null and remote-retrievable;
- two clean benchmark builds are byte-identical per language;
- plan generation is byte-identical across clean processes and has the exact
  counts 4/1,056/88/88/8;
- pure `plan` makes no filesystem change and invokes no child;
- every acquisition write is create-once and every interruption yields an
  auditable prefix with no rerunnable cell;
- runner and independent analyzer agree on all generated fixture outcomes;
- canonical protocol validation passes before and after freeze;
- the immutable artifact and snapshot transports have been exercised with
  non-benchmark fixtures and read-back verification;
- the global CPU lock is available and all other agents/jobs have explicitly
  paused CPU-intensive work before preparation or acquisition.

Until those conditions hold, the only accurate v6 status is
`prospective_design_blocked_before_preparation`.

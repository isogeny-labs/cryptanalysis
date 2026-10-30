# Native observation bridge for ECBench

This paired implementation supplies the native Rust library side of the
user's requested end-to-end ECBench assessment. The driver and frozen study
belong to crypto; this repository does not launch a second measurement.

An opt-in, scoped, single-thread observer records checked **prime** group
calls and exclusive cold/online phase clocks. It includes setup, factor-base
work, network construction, contraction, witness/relation checks, elimination,
recovery and failures. Scalar multiplications are expanded into group calls,
not charged twice. Diagnostics count attempted meter charges, not a complete
calibrated arithmetic inventory. Clocks include observation overhead. The
binary curve primitives do not acquire an end-to-end accounting adapter here.

`partial::solve_with_options` exposes the same collector with explicit selector
options/statistics. The original `partial::solve` wrapper retains its defaults.
The new control compares the full certificate, final RNG and metered work
between default/unobserved and explicit/observed runs. Session cleanup and
clock partitions are checked separately. No solver RNG, work policy, old
fixture, source recursion guard or dependency changes.

The final native package passes **96 tests** (64 library, 5 runner, 3 source
panel, 6 hash-prime, 1 factoring CLI, 10 finite-extension, 3 strict JSON and
4 width-extension), formatting, strict all-target clippy and Rust 1.78 all-target
checks. [Lossless raw logs](validation/) and the exact package
[source manifest](validation/native-sources.sha256) retain that scope.
The common new metrics, partial and finite-test files equal crypto's copies;
existing integration-specific differences remain intact.

The paired [diagram](pipeline.svg) and inspected [PDF](report.pdf) are the
crypto study's pre-data engineering handoff, with editable sources beside
them. They describe **planned** execution and pending gates. They are not a
measurement by this mirror. Crypto's registered prime-roster panel uses
10/12/14/16 field bits, eight public targets, nine arms, one warmup and five
measured rounds (1,728 planned executions). The ECBench arm uses this actual
native code rather than the separate whole-point tensor prototype.

No scientific/benchmark job or runtime-gain claim is made. Real execution still
requires a fresh current-source S3 checkpoint/readback and authenticated exact
native source/image/binary/job admission. Unknown/exhausted outcomes must be
retained and prevent full comparisons; native S remains a lower bound because
its arithmetic inventory is incomplete. The original frozen 60/24 A/B panel,
profiling, complete binary and schoolbook pipelines, both challenge scalars and
the independent general audit remain open.

Sources: the pinned
[Bochum reduction](https://github.com/bochum-crypto/subexponential-ecdl/tree/1ee44e562b1b9a50ea339f3b8f81112b5a24b96f),
current native source, crypto's `docs/ecbench/README.md` unit/replay contract,
the canonical experiment-protocol checker and maintained Iso Lab submission
contract. This is instrumentation/compatibility work, not a new theorem.

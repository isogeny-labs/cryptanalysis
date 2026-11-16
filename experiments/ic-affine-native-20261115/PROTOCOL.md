# Native affine S3 versus the best tested same-base IC control

[pcc:unverified] The preceding fixed-instance panel found MITM fastest on the
registered N15/N18 prefix bases. This experiment compares that same-base method
with a complete native affine S3 oracle, with and without bounded prefix
inverse-square preparation. The underlying projection is prior work; the
hypothesis is a full native implementation gain, not a new complexity theorem.

Reuse the exact instances and archived bases in
experiments/ic-s3-pipeline-20261115/instances.json: registered N15 dimension6,
58 rational lifts/29 sign columns, and N18 dimension7,134 lifts/67 columns.
Keep exact generators, fields, target subgroups, full-curve/cofactor-quotient
policy and the point/column archive digests. No curve or base search is allowed.

Freeze six new one-target fixture indices112..117 before target materialization.
Use the existing locked StdRng source law, exact scalar/point and walk seeds;
archive immutable candidate/workload identities before timing. Retain accidental
repeats rather than resampling. One fresh process per arm/target. Methods are
negation-folded MITM, affine-s3 inverse_cache=0, and affine-s3 inverse_cache=1.
The cache is target-independent, only for prefix subspaces of dimension<=12;
its complete construction belongs to setup. Affine residual limit12, with
complete subtraction fallback above it and for zero abscissa/identity targets.
A projection cap must never be reported as a refutation or silently omitted.

[pcc:unverified] All methods use m2, walk collection, incremental-gauss,50,000 trials. The
same-input correctness condition is every final scalar verified, exact base/
target/walk identities and a separate existing Python arithmetic replay.
Different methods may choose different valid witnesses and trial/rank paths;
retain those differences as part of full cost. Plain and negation rho execute
on each exact target/seed, with actual completion required for a reference.

Use all six permutations of the three methods across fixtures112..117. For
each curve/fixture run before/after baseline MITM fixture0; retain A/A ratios
outside0.85..1.15 and every outlier. No filtering or adaptive target selection.
Keep counted S model, context-inclusive counted S, complete cold interval wall,
wall-derived equivalents, calibration and outer process intervals separate.
The cold interval is fresh field/curve context plus first full run_pipeline:
base setup, oracle preparation, failed/successful queries, complete native
query work, group lifting, matrix operations and final verification. Input
loading, planted-input generation, benchmark calibration, replay and encoding
are outside it and reported separately. Native affine nanoseconds exclude
measured group-add intervals already priced by group-operation counters.

Build one default release probe (-j2, locked dependencies, unchanged release
profile) in a separate CPU4/8GiB job,900-second hard limit,780-second compile
limit. Preserve compile failures. Pin source/toolchain/binary hashes and manifest
smoke checks before timing. The timing allocation is one L4,4 requested CPUs,
8GiB,900-second hard limit,780-second controller cap,12seconds per process, one
pinned allowed CPU. CPU execution only. Kill a timed-out process group and
retain partial stdout/stderr; no automatic retry or cap extension.

Known gVisor placement remains unqualified. Qualified values remain null and
records stay invalid for promotion. A raw gain on these fixed inputs cannot
establish general curve scaling, cryptographic-size performance or mathematical
novelty. Preserve the earlier negative/slower-oracle comparison and build cap.
PCC ledger integration is separately pending custody-preserving reconciliation;
never rewrite either chain or use a gate waiver to promote a result.

Prior mechanism and source receipt: existing pdp-degree-heuristics/htsolver.py,
ic-bench/bench.py and the general-section reformulation cited in the preceding
NEXT_LEAD.md; KB revision9141e386254340a9bdba3036f2bb706a with its four exact/
negative/application/adjacent queries. Current owning native sources and the
previous48-pair full-pipeline dataset were inspected. No prior timing is used
as an arm or reference in this new comparison.

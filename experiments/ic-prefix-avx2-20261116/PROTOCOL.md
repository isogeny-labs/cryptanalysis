# AVX2 cached pair preparation, fixed arithmetic and registered bases

Continue the original broad IC performance goal. Test four-lane AVX2 plus
VPCLMULQDQ for independent cached pair sums, using the same two-fold sparse-tail
reduction as the existing AVX-512 scan. Keep the original field inverse and
matrix defaults; the preceding Euclidean/matrix factorial panel was negative
and noisy and is preserved without promotion.

Reuse exact registered N15/18/21/24/27 curves and archives from
experiments/ic-prefix-scale-20261116, d6/7/8/9/10 and29/67/127/257/531 sign
columns. No curve/base/target search or replacement. Four modes: mitm-prefix
(original scalar cached batch1024), mitm-vector64 (vector chunks64), mitm-vector
(vector chunks1024), mitm-vector4096 (vector chunks4096). These three fixed chunk
sizes are declared before target materialization; no adaptive selection or
omitted candidate. All opt-in, original defaults preserved. Runtime AVX2 and
VPCLMULQDQ checks plus exact sparse-tail field-shape checks guard the intrinsics.
Unsupported CPUs/fields/bases and exceptional/missing-cache pairs retain the
complete original arithmetic. Preserve ordered first witnesses and x+1 keys.

Freeze fresh fixtures288..311 per curve under existing locked StdRng seed/point/
walk law. All24 mode orders once per case, max_trials500000,m2,walk,batch sizes
as above. Same positive original-backend calibration, including lookups, unchanged
across all IC/rho arms. Full native preparation, including feature detection,
cache allocation/construction/cleanup, is charged once per target. Query/matrix
counts, exact target/seed and scalar verification must agree.

Two separate fresh rho processes per target, original arithmetic plain and
negation,2million trials each. Reverse reference order and move reference block
after IC on odd fixtures; before IC on even fixtures. Original cached prefix
fixture0 pre/post A/A bound0.85..1.15 with correct answers/frozen units. Require
all24targets for headlines; retain all caps,errors,OOMs,failed A/A,outliers and
duplicates. No replacements/retries/cap extension. Existing independent Python
arithmetic replays all completed IC/rho scalars.

Native preparation on L4CPU4/8GiB900s, CPU arithmetic only, locked-j2 default
release, compile780s. Additional bounded180s debug-library vector-kernel test
must exercise AVX2/VPCLMUL rather than skip, compare products to scalar over
at least50 accepted field widths. Overall native job still900s hard cap.
Match archived points/columns. Full first-witness-map checks compare full,
x-only,cached and vector builders at chunks1/7/64/1024/4096, all five fields.
Record vector_pairs and require actual vector use.15 synthetic unit-loader
checks. These are preparation correctness checks, no attack timing.

[pcc:unverified] Timing L4CPU4/8GiB900s, CPU execution only, pinned allowed CPU, controller780s,
child12s, RLIMIT_AS8GiB, GNU-time RSS/CPU/fault receipts. Separate requested/
exposed limits; unknown physical placement/throttle/OOM/memory properties stay
unknown. Frozen exploratory qualifiednull and recordinvalid for promotion.
Cold includes context, factor base, table/cache setup and cleanup, all queries,
matrix and scalar check. Materialization, calibration/loading, process startup
and independent replay remain separate. Bootstrap10000,seed20261116,linear
quantiles, paired medians, retain every row. Counts/phase models are not machine
instruction measurements. No GPU throughput, cryptographic-size, asymptotic or
broad-breakthrough claim. Known PCC custody fork stays unchanged.

Requirement evidence: exact source/toolchain/binary hashes; native vector unit
and full-map receipts; immutable candidates/workloads; all120four-way IC cases
plus240rho answers; arithmetic replay; all controls/resources; dated report,
editable diagrams and inspected PDF. Wider goal remains open after this panel.

Sources checked: owning suite/src/cryptanalysis/koblitz_fast.rs simd512 module
(primary source), existing scalar cached helpers and source ec41798826 report.
research-kb lexical “vpclmulqdq avx2 pair table abscissa reduction” returned
source:4adbd8e31fb746cbc2c0ed4125859db0,
cryptanalysis:docs/known-label-pair-index-20261029/README.md and
source:1ad1046a128d7931c21a95b44f264b6c,
cryptanalysis:docs/known-label-pair-index-20261029/review-20261101/source-fidelity-review.md.
Both published internal-analysis, no independent evidence. Primary records
separate algebraic scope, actual point creation, filtering, scalar replay and
setup; they do not establish this implementation's performance. No novelty or
absence-of-prior-art claim.

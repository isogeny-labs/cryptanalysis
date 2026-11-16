# Vector full-point arithmetic after one shared inversion

Original scope remains aggressive specialized native IC arithmetic and measured
algorithm performance. The preceding batch16 panel preserves an exploratory
collector comparison, not a promoted baseline or a general performance result.
The next candidate keeps that exact schedule and changes only point formulas.

Proposed kernel: use existing four-lane AVX2 carryless products/reduction after
FastCurve's simultaneous denominator inversion. Compute lambda, x and y in vectors:
lambda=(py+qy)/ (px+qx), x=lambda^2+lambda+px+qx+a,
y=lambda*(px+x)+x+py (binary field). Return FULL points for coefficient tracking,
not just table abscissae. Product-based squaring remains to isolate this change.
Reuse scratch; dispatch once per batch to ordinary PCLMUL or VPCLMUL where present.
Unsupported CPU/field shapes, exceptional pairs, noncanonical inputs and remainder
lanes retain the complete ordinary batch/scalar fallback. Actual vector-pair counts
must distinguish a request from execution. Keep existing defaults unchanged.

Correctness controls before timing: compare every output against existing full
scalar and shared-inverse additions, all accepted field widths (including >32),
normal and exceptional pairs, infinity/doubling/negation, empty/nonmultiple lengths,
reused scratch and append semantics. Force ordinary PCLMUL on wide hosts as well.
Verify full native/scalar/vector walker streams and a,b identities, unused work,
restarts, guards, matrix/rank/work, final scalars and independent Python replay.
No query law, base, target distribution, cap or matrix change is authorized by the
kernel comparison. Native host support must be checked on the actual allocation.

Predictions: vector reduction may reduce field-table loads and scalar dispatch in
point formulas; it may regress because gathers, scatter/packing or short16lanes
cost more. A source instruction count or component result is not a pipeline win.
Freeze a full protocol and fresh fixtures only after source/correctness controls,
then compare batch16 versus vector16 with identical schedules and current explicit
compute clocks. Preserve two failed AA controls in the prior panel and its invalid
promotion standing. No timing or new heldout inputs exist for this candidate yet.

Sources checked: KB revision9141e386254340a9bdba3036f2bb706a, lexical query
SIMD full point addition batched inversions AVX2 binary. Best relevant context:
source:c525825f5c51c500234cb8b8749a45dc, cryptanalysis:papers/frobenius-orbits/
sec-benchmarks.tex, primary-source/external-source/evidence none/not superseded;
source:c5b44937741b2f73ed2237dced16f1c1, docs/perf/PERFORMANCE_INDEX.md,
internal-analysis/published/evidence none/not superseded. Owning primary code read:
FastCurve.add_pairwise, Simd256.new/mul/reduce/add_cached, Gf2.batch_inv and the
new batched walker. Existing index-only vector kernels omit ordinates; this
candidate must compute and validate them. Atlas match saved in development log:
LEAD-RHO-batched-inversion-shared-pm is closed_known; its YAML read. This is known
engineering, with no mathematical novelty or prior-art-absence assertion.

Scaling lookup: docs/ic/BASELINES.md read (KB source:bac7966b7763504fc7923180cee41ada,
published internal analysis/evidence none/not superseded), plus current owning curve
registry and archive index. The larger registered baseline route uses different
factor bases/aimed collection, so a direct extension would change more than word
width. No prior ratio transfers. No curve/isogeny fact changes; canonical curve and
route graph set remains current. The next report will retain the outcome including
null/negative findings and all native captures/controls under standing gates.

# Exact N41 suffix sums fill the reciprocal trace-zero hyperplane

**The 3,544 four-column-compatible sums in a 64-by-64 sample of right-suffix
pairs have reciprocal binary rank 40 in the 41-bit field.** Every one of
their reciprocals has trace zero. Consequently, the exact right-suffix domain admits no additional
homogeneous `GF(2)`-linear reciprocal equality beyond trace zero: a linear
test that accepts every exact suffix sum also accepts every trace-zero
residual. This closes the proposed output-only *linear* inverse gate for the
frozen N41 construction and points the next search toward a condition that
couples two or more unresolved partial sums nonlinearly.

## Frozen source and measured censuses

The field is `GF(2)[t]/(t^41+t^3+1)` and the curve is
`y²+xy=x³+1`. The existing public-point panel has actual base size `B=256`
and 26 folded columns. Its public raw preimage and one fixed first-half pair
generate 1,711 eligible target-derived residuals. The right suffix uses two
rotated W6 source windows at Frobenius rotations 20 and 30; each has 64
transported source points and 1,956 valid distinct-column pairs. This is a
point-decomposition component (`candidate_id: null`).

The [residual protocol](protocol.json) froze the source, 1,712-point input,
both completed direct/S3 exact-join receipts, and checked Sage runtime before
the residual census. Checked Sage reconstructed every point, verified its
input and join status, and computed `1/x` in the declared polynomial basis.
The independently [verified result](analysis.json) is:

| Frozen reciprocal set | Count | Trace-zero values | Linear rank | Affine rank |
| --- | ---: | ---: | ---: | ---: |
| Positive plus 1,711 target-derived residuals | 1,712 | 1,712 | 40 | 40 |
| Pair sums before cross-pair column filtering | 4,096 | 4,096 | 40 | — |
| Four-column-compatible exact suffix sums | 3,544 | 3,544 | 40 | — |

The [suffix protocol](suffix_protocol.json) froze a second source-bound check
before its run. It selects the first 64 canonical distinct-column pairs in
each right source, then adds all 4,096 cross-rotation pair-point combinations.
Checked Sage found zero identity or zero-`x` exceptional sums and computed all
4,096 reciprocals. This initial census did not filter column overlap
**between** the two pairs. The subsequent [column-compatible audit](../n41_suffix_quadratic_span_20261012/RESULT.md)
removed 552 overlapping combinations and independently confirmed rank 40
on the retained 3,544 sums; it also found full degree-two feature rank.
The [suffix receipt](suffix_analysis.json) retains the original values and
selected source-pair indices. The direct and S3 predecessor receipts
agree that the positive residual has an exact suffix witness, while all 1,711
controls have completed exact misses under this fixed-second-pair input law.

The [independent audit](verify.py) checks frozen hashes, reconstructs the
canonical pair-index selection, verifies each residual reciprocal by
polynomial-basis field multiplication, recomputes the trace functional, and
eliminates both original reciprocal lists over `GF(2)` using a separate
binary-pivot implementation. It reports
`PASS_N41_OUTPUT_FIRST_LINEAR_SPAN_AUDIT 1712 40 4096 40`.

## Why the rank result excludes a linear gate here

The field trace `Tr: GF(2^41) -> GF(2)` is a nonzero linear functional, so
its kernel is a 40-dimensional binary space. Every four-column-compatible
suffix reciprocal lies in that kernel, and the corrected audit's rank is 40;
therefore their span equals the entire kernel. Any binary-linear functional
that vanishes on **all** exact suffix reciprocals must vanish on the trace
kernel. Such a functional is either zero or the trace functional. The
1,712 residual reciprocals are already trace zero, so another output-only
linear equality cannot reject any of them while retaining the exact suffix
domain. The statement concerns the frozen N41 suffix source and reciprocal
coordinate; it does not assert a corresponding rank for N131 or exclude a
nonlinear or jointly conditioned filter.

The [Lean proof map](PROOF_MAP.md) links the structural implication to a
checked Lean 4 theorem. The finite rank/field bridge is independently
replayed from the receipts and remains outside the current Lean module.

## Next experiment

Build a target-conditioned **joint** condition that retains at least two
unresolved first-half pairs and two unresolved suffix pair outputs. A useful
condition must reject complete first-half coefficient families before
opening their source masks or enumerating all suffix pair combinations. The
frozen N41 complete public-point fiber has 12 valid eight-column rows and
provides the positive coverage gate; the direct 1,956-pair suffix join is
the matched component baseline. Count whole-family rejection, preserved
positive rows, exact work and memory, and source-bound N131 projection before
another ordinary 600-second/4-GiB query. The present rank census gives no
reason to spend that query cap on another linear output-only constraint.

# Exact N41 suffix sums have full degree-two feature rank

**The 3,544 four-column-compatible sums in a frozen 64-by-64 right-suffix
panel have rank 821 across all constant, linear, and squarefree quadratic
features of the 40-dimensional reciprocal trace kernel.** In particular,
no nonzero polynomial of degree at most two on that kernel vanishes on every
exact suffix output. An output-only necessary equality of degree at most two
therefore cannot filter the frozen target-derived residuals while preserving
every exact suffix witness. A useful next constraint must couple partial
sums, use higher degree, or exploit a different representation.

## Source, filter, and rank

The parent [exact suffix census](../n41_output_first_inverse_20261012/RESULT.md)
uses `GF(2)[t]/(t^41+t^3+1)` on `y²+xy=x³+1`, with 64 transported W6
source points at each of rotations 20 and 30. Its first 64 valid canonical
pairs per rotation form 4,096 group sums with defined reciprocals. The
[initial frozen feature check](protocol.json) found rank 821 on all 4,096
using the archived reciprocal list. During source-law audit, we identified
552 combinations whose two pairs reuse a folded source column. Those rows
remain in the initial receipt but are excluded from the decisive result.

The [column-compatible protocol](valid_protocol.json) froze the full
four-column shield and source hashes before the corrected run. It retained
3,544 exact suffix sums. Every retained pair is internally distinct-column,
the four source columns are pairwise distinct, and each point is a group sum
of the declared transported source points. The [result](valid_result.json)
records all accepted source indices, 552 rejected indices by count, and 821
independent accepted row indices. The selected rows have reciprocal binary
rank 40 and degree-two feature rank 821.

| Frozen output set | Group sums | Cross-pair column rejects | Retained | Reciprocal rank | Degree-two feature rank |
| --- | ---: | ---: | ---: | ---: | ---: |
| First 64 exact pairs per right rotation | 4,096 | 552 | 3,544 | 40 | 821 / 821 |

For the degree-two matrix, one trace-pivot bit is removed to coordinatize
the trace-zero hyperplane. Each row is `1`, its 40 remaining coordinate
bits, and the 780 products `z_i z_j` with `i<j`. The [checked-Sage
audit](valid_audit.json) reconstructs the column filter from the frozen
source input and independently ranks the 821 selected rows over `GF(2)`;
it reports `PASS_N41_COLUMN_COMPATIBLE_SUFFIX_SAGE_AUDIT 3544 40 821`.
The [receipt verifier](verify.py) checks both frozen protocols, hashes,
counts, subset membership, and audit results. The checked Sage runtime was
saved before either rank job. This is an exact algebraic component census;
local elapsed times are not promoted as CPU speedups.

## Algebraic consequence and proof boundary

The `GF(2)` vector space of squarefree Boolean polynomials of degree at most
two in 40 variables has dimension `1+40+780=821`. Evaluating those
polynomials on the retained exact suffix reciprocals gives a matrix with
full column rank. Its kernel is zero, so a degree-at-most-two polynomial that
vanishes on **all** valid suffix outputs must restrict to the zero function
on the trace-zero hyperplane. Eliminating the dropped bit by the linear trace
equation maps every degree-at-most-two polynomial in the original 41
coordinate bits into this 821-dimensional space. The conclusion is for
this N41 source and the reciprocal output coordinate; it does not determine
the degree or cost of a joint target-conditioned constraint at N131.

The [proof map](PROOF_MAP.md) identifies the checked generic Lean span lemma
and the finite-field/rank bridge that remains outside Lean. Independent Sage
rank and source checks are preserved as empirical mathematical evidence.

## Next gate

Construct a target-conditioned equation involving **two unresolved
first-half pair outputs and two unresolved suffix pair outputs**. Freeze
positive and negative N41 public-point families before testing; require
preservation of all known positive rows and count whole-family rejection
before source masks are opened. Compare complete work with the existing
1,956-pair suffix join, then project the exact N131 source under one worker,
600 seconds, and 4 GiB. A single-output low-degree equality is exhausted
for this source panel.

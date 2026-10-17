# Exact aligned-quotient family gate and N131 code-label lower bound

An exact 17-bit quotient of the aligned N41 W9 source filters **2,485
two-code partial-sum families** against the frozen public target while
preserving the independently audited ordinary relation. With its three
suffix pair states fixed, two families pass the quotient gate and one
contains the exact required point. Across 64 independently sampled,
distinct-column suffix triples, only **eight of 159,040 family queries**
pass the quotient gate and none contains the exact required point. An
independent integer-field implementation replayed the complete census and
all 64 queries. At N131 W29, 512 source-valid code samples give a concrete
degree lower bound: **none of the 47 quotient labels is a Boolean
polynomial of degree at most two in the 28 code bits**. Independent Sage
reconstructed both roots per code and the matrix-nullspace certificate.

## Method and exact inputs

Both curves use `y²+xy=x³+1` with cofactor four. N41 is
`GF(2)[u]/(u^41+u³+1)`, prime subgroup order `549756390943`, curve ID
`EC1N41Ckb1h7d5e80d3c4d0`. N131 is
`GF(2)[u]/(u^131+u^13+u²+u+1)`, prime subgroup order
`680564733841876926932320129493409985129`, curve ID
`EC1N131Ckb1heb5f1998f20b`. The tested source uses five pair slots;
aligned rotations are `(0,0,12,12,24)` at N41 and `(0,0,36,36,72)`
at N131. The prior rank audit found branch-difference annihilators of
dimension 17 and 47, respectively.

For every distinct ordered pair of the 71 canonical N41 source codes in
slots 0 and 1, the checked-Sage producer stores all 16 signed group sums
and the set of projected reciprocal-x labels. The public point is the
archived raw point `(2026560328086,1928332930914)` at Frobenius
orientation 6. For a fixed suffix `S=P₂+P₃+P₄`, the target-dependent
required partial point is `N=Q-S`. The gate keeps a two-code family when
the label of `1/x(N)` is in its stored label set; exact equality of `N`
with one of its 16 points is checked separately. The positive suffix uses
the previously verified state IDs `(66,47,111)`, with source IDs
`(105,244)` in the first two slots. Every tested partial point has
nonzero x and is not the identity. The [Lean proof map](PROOF_MAP.md)
checks that an exact group witness survives this label gate.

The miss panel holds the same public point and source table fixed. It uses
Python `random.Random(202610171902)` to draw uniform IDs independently in
slots 2, 3, and 4, accepting triples with six distinct folded columns and
a nonexceptional required partial point. Sixty-four were accepted in 68
draws. The gate deliberately includes first-two-code families that would
share a suffix column, so its retention counts are conservative for a
complete distinct-column search. The [panel protocol](n41_panel_protocol.json)
was frozen before execution.

## N41 measured stage results

| Fixed suffix workload | Family queries | Quotient survivors | Exact point survivors | Audit |
| --- | ---: | ---: | ---: | --- |
| Archived ordinary relation suffix | 2,485 | 2 | 1, family index 1,529 | Independent full replay |
| 64 sampled suffix triples | 159,040 | 8 | 0 | Independent full replay |

The miss-panel query histogram is 57 suffixes with zero quotient survivors,
six with one, and one with two. The quotient positive query's second
family, index 2,356, is a label collision. The first producer precomputed
39,760 signed sums in **12.468 seconds** and the panel producer repeated
the table in **7.341 seconds**; shared-host timing variation is visible.
Each stored family has seven or eight distinct labels: 2,483 families have
eight, two have seven. Across the full table there are 19,880 distinct
partial x coordinates. The complete panel producer took 15.554 seconds,
including its 64 target-dependent suffix computations and scans. The
separate integer-field audits took 14.553 seconds for the first census
and 11.926 seconds for the panel. These are ordinary-host stage timings,
not a calibrated single-target IC/rho comparison. The protocols declare
one worker, 180 seconds, and 4 GiB; the completed scripts did not collect
an auditable peak-RSS trace, so the memory boundary remains unverified.

The [first N41 result](n41_result.json), [panel result](n41_panel_result.json),
and their [full replay](n41_audit_result.json) and
[panel replay](n41_panel_audit_result.json) retain every family index,
suffix query, source hash, and exact check. The initial pure-Python
implementation was [interrupted](n41_interrupted.json) after its
exponentiation-based inverse made the 39,760-sum census impractical;
its incomplete output was not used. The panel auditor's first invocation
failed on a protocol-key lookup before arithmetic; the
[preflight record](n41_panel_audit_preflight.json) and corrected
[frozen protocol](n41_panel_audit_protocol_v2.json) preserve that outcome.

## N131 source-code expression screen

The N131 seed mask is `898618`, leaving 28 canonical code bits. A fixed
PRNG seed `202610171856` supplied 2,100 distinct or rejected draws until
512 codes passed nonzero endpoint/product checks, both endpoint inverse
trace checks, and the two-root output quadratic. For each accepted code,
the producer computed both roots of `Cz²+pz+H=0` and checked that each
of the 47 annihilator projections agrees across those roots.

The 512-by-407 matrix of constant, 28 linear, and 378 quadratic Boolean
features has rank **407**. Its left kernel has dimension **105**. For
each of the 47 projected labels, the independent Sage auditor found a
nonzero left-kernel syndrome, after rebuilding all **1,024 roots** using
Sage polynomial factoring. Thus every degree-at-most-two expression is
inconsistent even on this fixed valid-code sample, and hence on the full
valid-code set. This exclusion concerns the 47 recorded quotient-basis
labels; it does not exclude a degree-three expression, a rational
representation, or an unrelated family certificate. The complete sample,
roots, labels, dual masks, and matrix results are in the
[producer](n131_result.json) and [independent audit](n131_audit_result.json).
An additional [group audit](n131_group_audit_result.json) constructed both
endpoint points for every sampled code by solving
`v²+v=x+1/x²`, `y=xv` with half-trace, then checked both signed pair-sum
reciprocal-x roots against the quadratic. It checked all 512 codes and
1,024 roots in **3.610 seconds**. The first generic Sage `lift_x`
implementation was [interrupted](n131_group_audit_preflight.json) because
it factors a polynomial per endpoint; the direct construction used the
versioned [frozen protocol](n131_group_audit_protocol_v2.json).

## Cost boundary and next discriminator

The N41 filter is highly selective **after** constructing all 16 partial
points for every two-code family. That construction already expands the
two free source-code families, and an exact point index can reuse the same
points. It therefore supplies a correct target-conditioned rejection
predicate and a measurement of selectivity, but not a reduction in the
dominant pair-family construction work. The N131 W29 source has 28 free
canonical bits before validity filtering. The independently replayed
[prior W29 source sample](../n41_n131_fivepair_w9_w29_20261017/RESULT.md)
already contains 16,677 source-valid distinct codes. Materializing
**all code pairs from that known subset as the current table does**
would require at least `C(16677,2)=139,052,826` family records and
`2,224,845,216` signed pair assignments. This is an operation-count
lower bound for this literal all-pairs construction; early column filtering
or a compressed representation would change the count. It is not a timed
N131 run. The table construction does not justify
promotion under the one-worker, 600-second/4-GiB public-point gate.
The sampled quadratic exclusion gives a separate implementation obstacle
for a compact per-code quotient lookup.

The next experiment should freeze a source-code rectangle representation
that computes the **set of reachable two-pair quotient labels without
enumerating its individual code pairs or 16 signed sums each**. It must
preserve the N41 orientation-6 witness, report rejection on an unseen
ordinary-suffix panel with all construction work charged, and provide an
explicit N131 memory and work bound before any 600-second public query.
This is a decomposition-stage experiment with `candidate_id: null`;
factor-base logs, final relation rank/linear algebra, target descent, and
paired same-point rho are not yet measured in this configuration.

Run `python3 -B verify.py` for the read-only
[terminal binding check](terminal.json) of frozen source, independent
audits, numeric outcomes, direct group bridge, and Lean axioms.

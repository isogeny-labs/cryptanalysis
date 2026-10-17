# Direct S3 inversion recovers a second pair code from a target residual

Solving the upper S3 link backward removes the two-code Cartesian product
from a fixed-residual query. For each first source code, the method uses
its two pair-output reciprocals, solves one quadratic for each, and
recovers each possible **second source product directly**. On the frozen
N41 W9 public relation and 64 ordinary miss suffixes, it examined
**9,230 quadratics**, returned **18,460 field roots**, and found exactly
one admissible source-code family: the independently verified public
relation. A separate integer-field implementation replayed all 65
queries. On an N131 W29 sample of 512 validated source codes plus two
constructed-control codes, it recovered the constructed first-two-pair
witness and found zero source-pair hits for the frozen public point with
that fixed constructed suffix; a separate binary-field replay matched
both queries.

## Exact method

Both instances use `E: y²+xy=x³+1` and the reciprocal coordinate
`z=1/x`. N41 is `GF(2)[u]/(u^41+u³+1)`, curve ID
`EC1N41Ckb1h7d5e80d3c4d0`, subgroup order `549756390943`.
N131 is `GF(2)[u]/(u^131+u^13+u²+u+1)`, curve ID
`EC1N131Ckb1heb5f1998f20b`, subgroup order
`680564733841876926932320129493409985129`. Both use the aligned
equal-rotation first two pair slots of the archived five-pair source.

Let `a` be the reciprocal x-coordinate of a first pair output and
`t=1/x(Q-S)` the target-dependent required two-pair sum coordinate,
where `S` is the sum of three fixed later pair states. The S3 equation
is exactly

`A b²+B b+D=0`, with `A=1+(at)²`, `B=at`, `D=a²+t²`.

Here `b` is the second pair output reciprocal. In the nonzero chart,
`B≠0`. If `A=0`, solve the linear equation. Otherwise set
`r=A D/B²`. When `Tr(r)=0`, half-trace gives `v²+v=r` and the two
solutions are `b=(B/A)v` and `b=(B/A)(v+1)`. For each nonzero `b`,
the fixed-seed pair law `C b²+q b+H=0` determines a unique second
source product `q=(C b²+H)/b`. A lookup in the valid source-product
table yields its code, if present. The implementation then tests the
few returned code families against full point addition. The
[Lean proof map](PROOF_MAP.md) gives checked algebraic identities and
the remaining finite-field and curve bridges.

The related [quartic inverse pilot](../n41_n131_two_code_quartic_inverse_20261017/result.json)
eliminated both pair-output roots into a degree-four polynomial in `q`.
It found exactly four field roots per first code on the same first five
N41 queries, and the same one source-code family. The direct construction
gets those candidates from two S3 quadratics, without generic quartic
factoring or enumerating all code pairs.

The normalized quadratic right-hand side also simplifies exactly to
`a²+a⁻²+t²+t⁻²`. The curve's reciprocal-x condition makes the trace of
each `a²+a⁻¹` and `t²+t⁻¹` zero, and trace is invariant under squaring.
Consequently the S3 solvability trace is zero for these curve
coordinates. The [trace census](trace_result.json) checked this identity
and zero trace on **all 9,230 N41** and **2,056 N131** tested
coordinate pairs. All producer quadratics split into two field roots.
This trace condition supplies no rejection on these rectangles; source
product membership supplies the observed selectivity.

## Frozen N41 public-point panel

The source has 71 valid canonical W9 codes and 284 signed pair states in
each slot, with rotations `(0,0,12,12,24)`. The raw public point is
`(2026560328086,1928332930914)` at Frobenius orientation 6. The
positive suffix uses archived state IDs `(66,47,111)` and retains the
verified first-two IDs `(105,244)`. The 64 miss suffixes are the
independently frozen panel from the earlier
[quotient experiment](../n41_n131_aligned_quotient_transfer_20261017/RESULT.md).
The [protocol](protocol.json) hashes every input and uses the checked
repository Sage launcher with one worker and a 180-second parent cap.

| N41 workload | S3 quadratics | Field roots | Source-code family hits | Exact point-family hits | Producer query wall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Archived ordinary relation suffix | 142 | 284 | 1, family 1,529 | 1, family 1,529 | 0.305 s |
| 64 frozen ordinary miss suffixes | 9,088 | 18,176 | 0 | 0 | 2.201 s summed; 0.027 s median |

All 9,230 S3 quadratics took the two-root case; no exceptional linear
or trace-miss case occurred on this frozen panel. The producer's
target-dependent intervals include suffix subtraction, quadratic
solving, source lookup, and point checking of returned families. Source
enumeration, pair-root construction, and process startup are outside
those intervals. The producer sampled **233,390,080 B self peak RSS**.
The [producer result](result.json) records every suffix, case count,
root count, candidate, and query interval. An independent
[integer-field audit](audit_result.json) checked the pair equations,
all 18,460 S3 roots, 65 source-product lookup results, and their match
to the previously audited exact point panel in **22.884 seconds**.

For context, the quartic pilot's first five identical fixed-suffix
queries used 355 generic polynomial root calls and 13.191 seconds
summed query wall. The direct method's corresponding five queries used
710 S3 quadratics and 0.373 seconds summed query wall. These are
ordinary-host stage measurements on separate runs; the algorithmic
change is the removal of quartic factoring, and these wall readings
are not a calibrated end-to-end IC speedup.

## N131 transfer control and work boundary

The N131 aligned W29 source uses seed mask `898618` and rotations
`(0,0,36,36,72)`. The frozen sample has 512 valid codes with both pair
roots independently checked against the curve group; the producer added
the two known constructed-control codes. The positive required partial
point is the sum of the first two constructed pair points. The ordinary
miss required partial point is the **frozen N131 raw public point** minus
the three later constructed pair points. This fixes those later states;
it is a source-sample control, not a search over their families.

| N131 fixed suffix | Source codes | S3 quadratics | Field roots | Source-pair hits | Producer query wall |
| --- | ---: | ---: | ---: | --- | ---: |
| Constructed positive | 514 | 1,028 | 2,056 | `(512,513)` | 2.618 s |
| Frozen public point, constructed suffix | 514 | 1,028 | 2,056 | 0 in this source sample | 2.149 s |

Every tested S3 quadratic again had two field roots. The producer's
sampled self peak RSS was **262,111,232 B**. The independently implemented
[GF(2^131) audit](n131_audit_result.json) reproduced all 2,056
quadratics, 4,112 roots, and both source-pair hit sets in **59.910
seconds**. Its exact inputs and bounds are frozen in the
[N131 protocol](n131_protocol.json) and
[audit protocol](n131_audit_protocol.json). The 4-GiB boundary was
observational for these completed processes; there is no independent
process-tree memory monitor or physical-host isolation receipt.

The preceding independently replayed W29 sample already contains
16,677 valid codes, so scanning even that known subset requires at
least 33,354 S3 quadratics **for one fixed suffix**. Scaling its measured
valid-code fraction to the full 28-bit code domain yields a sample-based
projection of 68,308,992 codes and about 136.6 million S3 quadratics
per fixed suffix. The latter is a prediction, not a complete source
census or a measured runtime. The three suffix pair families also remain
unresolved; this two-code inverse alone does not supply the joint
five-pair search needed by the frozen N131 public-point relation gate.

## Next experiment

The next exact gate should compose the direct inverse with a compact
constraint on **multiple still-free suffix code families**, preserving
their source labels and point signs. Its cheap N41 test must reject
whole suffix rectangles before enumerating their code products, retain
the orientation-6 witness, and charge construction plus every failed
query. An N131 run is warranted only after a source-bound one-worker
work and 4-GiB memory estimate fits the 600-second public-point
envelope. This remains a point-decomposition stage with
`candidate_id: null`; the useful relation-rank, final linear-algebra,
single-target recovery, and same-point rho phases belong to later
gates of the active goal.

Run `python3 -B verify.py` for the read-only
[terminal binding check](terminal.json) of frozen inputs, independent
replays, trace census, result counts, and Lean axioms.

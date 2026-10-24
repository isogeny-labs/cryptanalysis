# A target fingerprint excludes 131 of 132 N41 code rectangles

A **single symbolic quotient per complete 2×2 product-code rectangle**
tested the first 24 bits of the frozen public residual without specializing
the degree-eight root polynomial separately for its four code pairs or
extracting their roots. The equality-product residue became zero in **131
of 132 rectangles**; the sole survivor contains the independently replayed
ordinary witness family `(24,37)`. The one-worker Python producer finished
in **105.266 s** with observed self peak **28,180,480 B**. Checked Sage
verified every decision against all **4,224 exact roots** and confirmed
that exactly one of the 528 covered code pairs contains the full residual
coordinate.

## Construction and controls

The instance is `EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[t]/(t^41+t^3+1)`, W8 seed 56, the archived first two pair slots,
and public residual index 0 after the frozen five-state suffix. At depth
`(6,6)`, 132 admissible rectangles contain the complete Cartesian product
of two left and two right product codes. They cover 528 of the archived
1,554 admissible two-code families. A first freeze incorrectly counted all
134 four-family rectangles as complete 2×2 products; its assertion failure
is preserved, and the corrected frozen protocol excludes the two incomplete
rectangles. `candidate_id` is `null` because this is a point-decomposition
component.

The coefficient ring is
`R=GF(2^41)[p,q]/((p+p₀)(p+p₁),(q+q₀)(q+q₁))`, with basis `1,p,q,pq`.
The worker specializes the archived 170-term polynomial `H(p,q,U)` once
in `R`, then works in `R[U]/H`, of dimension 32 over `GF(2^41)`.
It computes the quotient element `z=U/(1+U)=1/x` and the trace-dual
polynomials for the selected representation bits of `z`. For target bit
`tᵢ`, multiply by `bᵢ(z)` if `tᵢ=1`, otherwise by `1+bᵢ(z)`.
The product is an exact Boolean indicator at every root. A zero quotient
residue proves that no root in any of the four code pairs matches the
selected target bits. The worker stops a rectangle as soon as the product
is zero.

| Bits checked | Rectangles rejected / 132 | Families covered by rejected rectangles | Surviving rectangles |
| ---: | ---: | ---: | ---: |
| 8 | 108 | 432 | 24 |
| 12 | 130 | 520 | 2 |
| 16 | 131 | 524 | 1 |
| 24 | 131 | 524 | 1 |

The bits were fixed as positions `0..23` before the fingerprint run.
The only survivor is prefix `(38,53)` with case indices
`(965,966,1004,1005)`; the exact residual is in case `966`. The median
rectangle used six bit factors, and 131 rectangles stopped by bit 13.
The independent Sage audit recomputed all 4,752 specialized polynomial
coefficients, all 4,224 roots, and 16,896 checkpoint indicators. It also
confirmed the sole exact coordinate family. The pinned Sage runtime and
all source hashes are in `sage_runtime_info.json` and `hash_protocol.json`.

## Iteration evidence and cost

The first two frozen rectangles established the unspecialized quotient:
one known rejection and the witness control. A sweep of one cubic bit
`z₂z₅z₈` across all 132 complete rectangles rejected five in 49.573 s;
Sage checked all 4,224 roots. A separate 32-rectangle training set chose
15 ordinary cubic-feature bits. Those covered 32/32 training rectangles
but only 21 of the 98 full-feature-rejectable rectangles in a disjoint
100-rectangle holdout. The symbolic holdout reproduced the 21 decisions
in 106.271 s; Sage checked 3,200 roots and 41,664 residue/root values.
This led to the direct equality-product test above.

The fingerprint run's exclusive measured phases were 0.024 s trace-dual
setup, 1.244 s symbolic H construction, 0.885 s chart inversion, and
103.108 s fingerprint trace/product work; the remaining 0.005 s is loop
and serialization overhead. These sum to the 105.266 s recorded wall
interval up to rounding. The producer enforced a 300 s alarm and checked
its own RSS against 4 GiB; the timing is an ordinary-host component
diagnostic, not a physical-host isolation measurement. Independent Sage
replay took 24.625 s in its audit interval after checked-launcher startup.
`verify.py` checks all frozen hashes, failure preservation, stage receipts,
witness retention, and Lean output.

## Transfer gate

The result supplies a compact **target-conditioned leaf certificate** for
several product codes at once. Its current coefficient ring still has
dimension proportional to the number of code pairs in a rectangle, and the
public residual was formed after five suffix states were fixed. The next
experiment must keep additional suffix codes free while proving the
indicator zero over a larger product-code region without enumerating its
Cartesian code pairs. Freeze unpinned N41 positives and ordinary negatives,
then measure complete source traversal, early rejection, witness replay,
memory, and charged target-dependent time before the N131 W23 public-point
gate under one worker, 600 seconds, and 4 GiB.

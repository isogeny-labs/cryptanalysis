# Proof map for the global cross span

| Result | Declaration or certificate | Hypotheses and status |
| --- | --- | --- |
| Every cross term `z²+z` has absolute trace zero | `BilinearGate.artin_schreier_trace_zero` in `../n41_bilinear_rank_screen_20261013/BilinearGate.lean` | Generic additive trace preserving squaring; checked in pinned Lean 4.34.1 by the prior experiment. |
| The complete N41 W6 output-family union has dimension 40 | `result.json` coordinate pivot certificate and `audit_result.json` | Native census covers all 2,048 declared product families; checked Sage independently reconstructs the nine families furnishing the 40 lower-bound pivots. The trace-zero equation gives the upper bound. |
| Target-conditioned cross span has dimension 40 | `result.json` cross pivot certificate and independent Sage audit | Bilinearity reduces the complete cross set to products of a coordinate-union basis. Sage recomputes the 40 independent pivot values. Absolute trace zero gives the upper bound. |
| Concrete field trace pairing is nondegenerate | Native full 41-row pairing elimination and independent Sage rank 41 | Exact polynomial-basis `GF(2^41)` representation; the general field theorem is not imported into Lean here. |
| Universal cross-annihilator is `span{1}` | Written proof in `RESULT.md` plus the three rank certificates | A 40-dimensional cross span in a 41-dimensional space has a one-dimensional annihilator under the nondegenerate trace pairing; `1` belongs to it by the checked trace identity. Concrete rank/certificate-to-Lean bridge remains open. |

The complete source proof uses two linearity facts. For fixed `t`,
`(tcd)²+tcd` is additive in `c` and in `d` over `GF(2)`. Every member of
every family lies in the 40-dimensional span of the archived coordinate
pivots. Therefore every cross term lies in the span of the 1,600 pivot
products. The archived 40 cross pivots are independent, while the
Artin-Schreier trace law bounds the span by the 40-dimensional trace-zero
hyperplane. Nondegeneracy of the recorded 41-by-41 trace-pairing matrix
then gives a one-dimensional annihilator; the multiplier `1` is in that
annihilator. This establishes the stated finite result.

The prior Lean module has a pinned toolchain and `#print axioms` audit.
This experiment's rank statements remain computational certificates plus
an independent replay; a faithful Lean import of the exact field,
family-basis construction, and 40-pivot certificates remains open. No
weaker Lean statement is presented as a proof of the full finite census.

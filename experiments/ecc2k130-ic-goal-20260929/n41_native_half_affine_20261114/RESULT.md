# Native half-affine gate rejects 99.8% of N41 families; direct rank remains faster

The native two-half affine gate reproduces the exact frozen N41 four-axis result: it retains 495 of 248,640 chart/family combinations, checks 3,960 individual roots against actual source products, and returns the unique witness `(chart 0, left 24, right 37, root 2, third 10)`. In a frozen alternating run on the same input, its target-dependent loop took 1.403–1.481 s versus 1.143–1.151 s for the prior direct-rank kernel. The gate is selective, but its extra span construction costs more than testing all 1,989,120 roots by direct rank on this workload.

## Method and frozen comparison

The field is `GF(2)[t]/(t^41+t^3+1)` on `EC1N41Ckb1h7d5e80d3c4d0`. The input is the archived public raw point and 160 residual charts, each with 1,554 admissible first-two-code families of eight roots. For each root the third-product resultant is `c0+c1*p+c2*p²`. The native gate forms the binary span of `c1*b+c2*b²` for seven independent product-basis vectors and four roots in each half, plus the three root-constant differences. If the half's anchor constant is outside that span, no third-source product can solve any of its four equations. The existing `AffineGate.true_witness_passes_half` Lean theorem proves this implication under its stated characteristic-two and source-basis hypotheses; the concrete field, chart, and source rows are checked by the frozen Sage archive and this native replay. This experiment adds an implementation and measurement, not a new theorem.

The [protocol](protocol.json) fixes the input/source SHA-256 hashes, ABBA order, and expected census. [The runner](run_abba.py) recompiles both sources using the same compiler flags, validates every output, and checks the complete native affine rank histograms against the archived Sage result. The existing independent checked-Sage verifier was rerun and returned `PASS_N41_AFFINE_GATE_INDEPENDENT_RECEIPT`, including the raw-point sum and 14 distinct folded columns.

| Order | Method | Target-dependent loop | Root-level work | Exact hit |
| ---: | --- | ---: | ---: | --- |
| 1 | half affine | 1.48125 s | 3,960 retained roots checked against source products | `(0,24,37,2,10)` |
| 2 | direct rank | 1.15079 s | 1,989,120 rank checks | same |
| 3 | direct rank | 1.14310 s | 1,989,120 rank checks | same |
| 4 | half affine | 1.40253 s | 3,960 retained roots checked against source products | same |

The affine-to-rank loop-time ratio spans 1.22–1.30 across these observations. Both loops exclude input parsing and process launch; all failed gate checks are charged. The [raw result](abba_result.json) records the four exact JSON rows, binaries, source hashes, compiler, and commands. This is an ordinary shared macOS arm64 host without a Tier 0 or Tier 1 isolation receipt. The input is a fixed-suffix point-decomposition stage, so `candidate_id` remains null; these times do not represent a complete one-target IC/rho comparison.

## Decision for the degree-131 transfer

The direct-rank kernel is the implementation baseline for the same frozen N41 family search. The half-affine gate remains a lossless way to reject an entire family before individual source checks, but this measured implementation does not improve that search's loop time. A degree-131 transfer needs an exact W23 first-two-root family and third-product source span, a constructed witness, and a separately frozen ordinary public query. Its cost must include family generation and all rejected cases; selectivity alone is insufficient. A different gate must remove a larger outer code family before computing these per-root coefficients to change the full N131 search cost.

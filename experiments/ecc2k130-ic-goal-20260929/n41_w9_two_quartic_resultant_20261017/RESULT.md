# An exact two-quartic joint gate for the N41 W9 source

## Contribution

The last two W9 source pairs admit an **exact fixed-code, target-conditioned joint equation in the preceding reciprocal coordinate `z`**, with the shared intermediate reciprocal `w` eliminated. For each allowed final code, its quartic in `w` splits into four source roots. The joint gate is the product of the preceding-pair quartic evaluated at those roots; it vanishes exactly when the two quartics share a root. A checked Lean theorem proves this split-root criterion under explicit field, factorization, and nonzero-leading assumptions.

The frozen N41 panel passed: one archived relation satisfies the gate, and **0 of 32 source-valid reachable controls** do. All 33 panel code pairs produce a degree-16 polynomial with all 17 coefficients nonzero and 16 distinct field roots. A separate complete leading-coefficient census found **degree 16 for all 5,041 allowed code pairs**. This establishes that the elimination is an exact algebraic representation; on this source its degree does not shrink the 16 signed state combinations available to each code pair. Coefficient sparsity beyond the 33 panel pairs remains unmeasured.

## Equation and proof

Work over `F=GF(2)[u]/(u^41+u^3+1)` on `y²+xy=x³+1`, curve ID `EC1N41Ckb1h7d5e80d3c4d0`, subgroup order `549756390943`. The public point is `Q=(1936680952394,910597499030)`, with reciprocal `t=1988710223364`. The five aligned pair rotations are `(0,0,12,12,24)`. Each slot has 71 allowed W9 codes and four signed states per code. Its actual five-pair IC pipeline remains unspecified, hence `candidate_id: null`.

For source-pair product `p`, rotation-dependent `H`, `C=1+H`, and reciprocal inputs `x,w`, define

`B=xw`, `A=1+B²`, `D=x²+w²`, `M=AH+CD`, and

`R(w;x,p,H,C)=AD p²+B M p+M²+CH B²`.

The preceding-pair equation is `R3(w,z)=R(w;z,p3,H3,C3)`; the final-pair equation is `R4(w)=R(w;t,p4,H4,C4)`. For a fixed final code, let its four independently checked field roots be `w0,...,w3`. The implicit joint equation is

`J(z;p3,p4,Q)=∏_{i=0}^3 R3(wi,z)=0`.

Since `R4` has degree four, nonzero leading coefficient, and exactly these four field roots, `J=0` if and only if `R3` and `R4` share a field root. The Sylvester resultant `Res_w(R3,R4)` differs from `J` by the nonzero fourth power of the leading coefficient of `R4` when the nominal degree in `w` is four. This normalization preserves the zero set. The [proof map](PROOF_MAP.md) separates the checked split-root theorem from the remaining concrete-polynomial formalization bridges.

Write `h=H3`, `c=C3`, and `p=p3`. Expanding `R3` as a polynomial in `z` gives coefficients from degree zero to four:

| Power of `z` | Coefficient |
| --- | --- |
| 0 | `(h+c w²)²+w² p²` |
| 1 | `w p (h+c w²)` |
| 2 | `(1+w⁴)p²+c h w²` |
| 3 | `w p (h w²+c)` |
| 4 | `w²p²+(h w²+c)²=(wp+h w²+c)²` |

The last identity is checked as `SharedQuartic.quartic_lead_square`. It gives a cheap exact test for degree four of each factor and therefore degree 16 of each fixed-code product.

## Frozen experiments

The [panel protocol](panel_protocol.json) hashes its source, archived witness, 2,048 reachable controls, and the draw code before selection. Seed `41019` selected one source-valid preceding-pair state for each of the first 32 controls while preserving ten distinct factor-base columns. The positive panel row uses the checked intermediate `w=2127775291906` and preceding `z=1795929544156`. Every Sage run used this repository's checked `./sage` launcher; its [runtime receipt](sage_runtime_info.json) was saved before arithmetic timing.

| Check | Exact result | Arithmetic wall | Peak self RSS |
| --- | ---: | ---: | ---: |
| All 71 final-code quartics split into their four archived roots, plus 33 pairwise resultants and group replays | pass; positive 1/1, control hits 0/32 | 4.407 s | 242,679,808 B |
| Symbolic `J(z)` on 33 frozen code pairs | all degree 16, 17 nonzero coefficients, 16 distinct field roots | 3.427 s | 256,557,056 B |
| Leading coefficient census | 20,164 constituent quartics nonzero; 5,041/5,041 products degree 16 | 1.068 s | 188,137,472 B |

The arithmetic intervals exclude launcher verification and process startup. These are ordinary-host algorithmic diagnostics, not CPU-isolated IC/rho timings. The [quartic panel result](run_result.json), [symbolic result](symbolic_result.json), and [leading census](leading_result.json) retain hashes, all row statuses, exact counts, phase times and memory. `run_sage.py` also independently replays the curve group law for every panel row; the positive row sums to `Q` and all 32 controls do not.

The first quartic run failed in Sage setup because its field element lacks `half_trace`; the second passed arithmetic assertions but failed JSON serialization of Sage integers. Their exact source/protocol snapshots and [failure receipts](attempt1.json), [second failure receipt](attempt2.json) are retained. Two full-polynomial 5,041-pair census attempts reached their frozen 120-second arithmetic caps; [attempt one](census_attempt1.json) and [attempt two](census_attempt2.json) are `BOUNDED_UNKNOWN` for full coefficient sparsity. The cheaper leading-coefficient census then completed the all-pairs degree question without treating either cap as an algebraic counterexample.

## Consequence and next experiment

There are `71²×16=80,656` raw signed last-two-pair assignments. The preceding independently replayed support has 79,424 usable `(w,z)` rows after 1,232 column-collision exclusions. The joint polynomial represents this same geometry at fixed codes; its useful prospect is a smaller **Boolean implementation of the elimination**, not fewer fixed-code roots. The next preflight should construct a direct resultant or structured product circuit with free code bits, measure its full clause/variable count and positive/control propagation against the existing joint-residual BDD, then run an unpinned same-budget ordinary query only if that circuit materially lowers encoding cost. An N131 run remains gated on a completed N41 query and a projected one-worker/600-second/4-GiB envelope.

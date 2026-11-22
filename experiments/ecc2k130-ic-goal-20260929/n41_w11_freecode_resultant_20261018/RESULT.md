# Free-code two-pair resultant on N41 W11

**A 13-term target-conditioned polynomial links both still-free source
products and admits a five-multiplication Boolean circuit.** On the
frozen N41 positive residual, one-worker CryptoMiniSat solved its
2,259-variable XCNF in **33.108 seconds**. Independent model replay
checked all 6,881 CNF clauses and 458 native XOR rows, decoded source
codes `(253,63)`, and reconstructed the exact signed state pair
`(278,74)` summing to the residual. The earlier exact two-pair circuit
on this same positive point reached its 120-second parent cap with
`BOUNDED_UNKNOWN`; its 3,321 AND gates compare with **1,781** here.

The polynomial itself was exhaustively evaluated on all
`281²=78,961` source-code pairs for each of 25 frozen residuals:
**1,974,025 code-pair tests**, with exactly one zero pair, the
verified positive `(253,63)`. The other 24 ordinary target-derived
residuals had zero polynomial roots. A separate one-worker solver run
on the first ordinary residual returned UNSAT in 92.255 seconds;
the native finite-domain census independently found zero code-pair
roots for that point. These are exact N41 two-pair component results.
The full IC method and target handling remain unspecified, so
`candidate_id` is `null`.

## Instance, inputs, and equation

The field is `GF(2)[u]/(u^41+u³+1)` and the curve is
`y²+xy=x³+1`, ID `EC1N41Ckb1h7d5e80d3c4d0`, subgroup order
549,756,390,943 and cofactor four. The W11 fixed-seed pair source
has 281 valid codes; first and second pairs use Frobenius rotations
12 and 24. The positive target is
`R=(1434452595080,1460136977354)`, derived from the independently
replayed unpinned public relation. The 24 ordinary residuals are the
frozen public raw point minus three random distinct-code source
pairs, as specified in the [prior panel](../n41_w11_target_block_filter_20261018/RESULT.md).
Both source codes stay free in the SAT queries. Planted knowledge of
the positive witness is used only to check construction and replay.

For the first pair reciprocal `w` and product `p₁`, the source equation
is `C₁w²+p₁w+H₁=0`. The target-conditioned equation for its second
pair is the prior quartic `R(w;t,p₂,H₂,C₂)`, where `t=1/x(R)` and
`p₂` is the second source product. Divide `R` by the first quadratic,
obtaining the remainder `r₀(p₁,p₂)+r₁(p₁,p₂)w`. Eliminating `w`
gives

`F_R(p₁,p₂)=C₁r₀²+p₁r₀r₁+H₁r₁²=0`.

The [Lean theorem and proof map](PROOF_MAP.md) show that, when the
first quadratic splits into its two source reciprocals and the
remainder identity holds, this condition is equivalent to a common
field root. The [checked-Sage export](export_result.json) verifies the
symbolic remainder over `F[p₁,p₂]` for every frozen target. Each
resultant has bidegree `(4,4)` and the same 13-monomial support:
nine terms with even powers of both products and four terms with odd
powers of both. Thus it can be evaluated as
`A(p₁²,p₂²)+p₁p₂ B(p₁²,p₂²)`, with three field products inside
`A,B` and two for the final factor. Source products are binary linear
in their ten free code bits, and squaring is binary linear.

## Measured checks

| Check | Result | Measured interval or size |
| --- | --- | ---: |
| Symbolic export for all 25 target points | exact remainder; 13 terms and bidegree `(4,4)` each | 1.250 s arithmetic |
| Native complete code-pair census with direct group replay of every hit | one positive root and witness; zero roots on 24 ordinary points | 1.627 s total native process; 1,974,025 pairs |
| Positive resultant XCNF construction | known witness satisfies all clauses and XOR rows | 1,781 AND gates; 2,259 variables; 6,881 CNF clauses; 458 XOR rows |
| Positive SAT, one worker, 120 s parent/4 GiB RSS caps | verified code pair and group witness | 33.108 s; 36,323,328 B sampled combined peak RSS |
| First ordinary SAT, same caps | solver UNSAT, independent census zero roots | 92.255 s; 35,258,368 B sampled combined peak RSS |

The [native census](census_result.json) checked all code pairs for
each input and used curve addition to replay every polynomial zero.
Its parent [receipt](census_receipt.json) hashes the binary, source
table and 25-target coefficient input. The [positive model
receipt](model_result.json) independently checks the entire solver
assignment and curve sum. The [terminal verification](verification_result.json)
binds all protocol hashes and row counts. The [Lean check](lean_check.log)
records axioms for the structural elimination theorem. The SAT runs
were performed sequentially with one solver worker and a 4 GiB
sampled-RSS cap; these ordinary-host stage times do not meet the CPU
isolation contract for a complete IC/rho comparison.

The earlier exact circuit used 4,315 variables, 3,321 AND gates,
10,185 CNF clauses and 810 XOR rows, and its positive query was
`BOUNDED_UNKNOWN` at a 120.302-second parent wall. The current
construction removes pair-root and intermediate-output Boolean
variables from that two-pair query. A solved positive after an earlier
cap is a stronger stage outcome; the capped old run does not supply a
numeric timing ratio.

## N131 transfer gate

The result identifies a compact target-conditioned *two-pair*
subproblem. A complete N131 W33 source has 32 free code bits in each
pair product; its validity constraints cannot be enumerated as the
743 forbidden-code clauses used per side here. A transfer must encode
the exact nonzero, trace and inverse conditions for both free codes,
then measure circuit construction, positive propagation, ordinary
query cost, memory, and relation-search work under the one-worker
600-second/4-GiB N131 envelope. The N131 public-point run is gated on
that source-bound projection. Even a fast two-pair oracle must be
charged across the target-conditioned residuals needed for one
ordinary factor-base relation and then the full IC pipeline.
